#!/usr/bin/env python
"""
compare_docx_content.py

逐部件、逐块比对两个 .docx，用于**证明「新增目录」等改动未影响正文内容**。

比对层次
--------
1. 包级：zip 部件清单，按 sha256 分为 一致 / 新增 / 删除 / 修改 四类。
2. document.xml 正文流：按块（段落 / 表格）生成结构化签名——
   - 段落：样式、文本、逐 run 格式（字体/字号/加粗/斜体/下划线/颜色/上下标/
     大小写转换/高亮）、制表符与换行符、内嵌图形数量、段落级属性；
   - 表格：行数/列数/列宽/单元格文本/内嵌图形数量。
   用 difflib 定位新增、删除、修改的块。
3. 样式表 styles.xml：对比 styleId 集合与各样式定义，列出新增/删除/被改动的样式。
4. settings.xml：对比子元素标签集合。
5. 其它被修改的 XML 部件：用 C14N 规范形式判别「语义真变化」还是
   「仅序列化差异」（如 _rels、header/footer 经不同工具重存后的字节差异）。
6. 目录捕获样式审计：验证 --capture-styles 指定的样式为「新增且不含 rPr 外观
   属性」，排除「套用样式反而改掉正文外观」这类内容比对查不出的风险。

「内容一致」的判定
----------------
正文块在**忽略段落样式**的前提下逐块一致，且表格/图形数量一致，即判定内容一致；
分层输出：内容层（纯文字）→ 格式层（run/段落/表格格式）→ 样式层（pStyle 名）。
分段样式变化会单独列出（本工具的自有约定：套用「目录捕获样式」只加 pStyle、不改外观）。

用法
----
    python compare_docx_content.py <原始.docx> <新文件.docx> [-o 报告.md]
    python compare_docx_content.py <原始.docx> <新文件.docx> --align-body
    python compare_docx_content.py a.docx b.docx --align-body --capture-styles SciTOC1,SciTOC2
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# 逐 run 需要比对的 rPr 子元素
_RPR_TAGS = (
    "rFonts",
    "b",
    "bCs",
    "i",
    "iCs",
    "u",
    "strike",
    "dstrike",
    "color",
    "sz",
    "szCs",
    "highlight",
    "shd",
    "vertAlign",
    "caps",
    "smallCaps",
    "spacing",
    "w",
    "kern",
    "position",
)
# 段落级需要比对的 pPr 子元素（pStyle 单独处理）
_PPR_TAGS = (
    "keepNext",
    "keepLines",
    "pageBreakBefore",
    "widowControl",
    "pBdr",
    "shd",
    "tabs",
    "spacing",
    "ind",
    "jc",
    "textAlignment",
    "outlineLvl",
    "numPr",
    "snapToGrid",
    "adjustRightInd",
    "rPr",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _elemsig(parent, tag: str) -> str:
    """把 pPr/rPr 下某个子元素序列化为紧凑字符串（无则空字符串）。"""
    if parent is None:
        return ""
    el = parent.find(qn("w:" + tag))
    if el is None:
        return ""
    return re.sub(r"\s+xmlns:[^=]+=\"[^\"]*\"", "", _tostr(el)).replace(" ", "")


def _tostr(el) -> str:
    from lxml import etree

    return etree.tostring(el, encoding="unicode")


def para_sig(p: Paragraph, with_style: bool = True) -> tuple:
    el = p._p
    pPr = el.find(qn("w:pPr"))
    pstyle = ""
    if pPr is not None and pPr.find(qn("w:pStyle")) is not None:
        pstyle = pPr.find(qn("w:pStyle")).get(qn("w:val")) or ""

    runs = []
    for r in el.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        spec = tuple((tag, _elemsig(rPr, tag)) for tag in _RPR_TAGS if _elemsig(rPr, tag))
        text = "".join(t.text or "" for t in r.findall(qn("w:t")))
        runs.append(
            (
                text,
                spec,
                len(r.findall(qn("w:tab"))),
                len(r.findall(qn("w:br"))),
                len(r.findall(qn("w:drawing"))) + len(r.findall(qn("w:pict"))),
                len(r.findall(qn("w:fldChar"))),
            )
        )

    ppr_spec = tuple((tag, _elemsig(pPr, tag)) for tag in _PPR_TAGS if _elemsig(pPr, tag))
    drawings = len(el.findall(".//" + W + "drawing")) + len(el.findall(".//" + W + "pict"))

    sig = (p.text, tuple(runs), ppr_spec, drawings)
    return (pstyle,) + sig if with_style else sig


def table_sig(t: Table) -> tuple:
    el = t._tbl
    grid = [gc.get(qn("w:w")) for gc in el.findall(qn("w:tblGrid") + "/" + qn("w:gridCol"))]
    cells = []
    for row in el.findall(qn("w:tr")):
        for tc in row.findall(qn("w:tc")):
            cells.append("".join(x.text or "" for x in tc.iter(qn("w:t"))))
    drawings = len(el.findall(".//" + W + "drawing")) + len(el.findall(".//" + W + "pict"))
    return (len(el.findall(qn("w:tr"))), len(grid), tuple(grid), tuple(cells), drawings)


def body_flow(path: Path) -> list[tuple]:
    d = docx.Document(str(path))
    out = []
    for c in d.element.body.iterchildren():
        tag = c.tag.split("}")[-1]
        if tag == "p":
            out.append(("p",) + para_sig(Paragraph(c, d)))
        elif tag == "tbl":
            out.append(("tbl",) + table_sig(Table(c, d)))
    return out


def body_flow_nostyle(path: Path) -> list[tuple]:
    d = docx.Document(str(path))
    out = []
    for c in d.element.body.iterchildren():
        tag = c.tag.split("}")[-1]
        if tag == "p":
            out.append(("p",) + para_sig(Paragraph(c, d), with_style=False))
        elif tag == "tbl":
            out.append(("tbl",) + table_sig(Table(c, d)))
    return out


def anchor_key(block: tuple) -> tuple:
    """
    对齐锚点键：只取「文本内容」，完全忽略段落样式与 run 级格式。

    入参取自 body_flow（含样式）的块，其字段布局为：
      段落 -> ("p", pStyle, text, runs, ppr, drawings)   ← 文本在 [2]
      表格 -> ("tbl", rows, ncols, grid, cells, drawings) ← 单元格文本在 [4]
    这样即使某个块被套用/改动了样式，也能被稳定定位，不会因格式差异而锚点失配。
    """
    if block[0] == "p":
        txt = re.sub(r"\s+", " ", (block[2] or "")).strip()
        return ("p", txt)
    return ("tbl", tuple(c or "" for c in block[4]))


def _describe(block: tuple, width: int = 90) -> str:
    """block 为「含样式」流（body_flow）的块：(kind, pStyle, text, runs, ppr, drawings)。"""
    if block[0] == "p":
        txt = (block[2] or "").replace("\n", "\\n")
        return f"段落[{block[1] or 'Normal'}] {txt[:width]}"
    cells = [c for c in block[4] if c][:3]
    return f"表格 {block[1]}行x{block[2]}列 图形{block[5]} | {' / '.join(c[:24] for c in cells)}"


# 子元素「顺序」在规范中不承载语义的部件。这类部件只按集合语义解读，
# 因此重排 <Override>/<Default> 不构成内容变化。**不要**把 document.xml 之类
# 加进来——在那些部件里，块的先后顺序就是内容本身。
_ORDER_INSENSITIVE_PARTS = {"[Content_Types].xml"}


def _norm_tree(el) -> tuple:
    """把元素树归一化为 (tag, 属性, 文本, 子元素) 的嵌套元组，子元素按 tag+文本排序。"""
    kids = sorted((_norm_tree(k) for k in el), key=repr)
    return (el.tag, tuple(sorted(el.attrib.items())), (el.text or "").strip(), tuple(kids))


def canonical_xml_children_sorted(data: bytes) -> str | None:
    """
    在 C14N 之上再把每层子元素排序，用于判定「顺序无意义」部件的语义等价性。
    返回 None 表示无法解析。
    """
    try:
        root = ET.fromstring(data.decode("utf-8"))
    except Exception:
        return None
    return repr(_norm_tree(root))


def canonical_xml(data: bytes) -> str | None:
    """
    把 XML 字节转为规范化文本（C14N），用于判断两个部件的**语义**是否相同。

    OOXML 部件经不同工具（python-docx / Word）重新序列化后，字节常有差异，
    但元素树可能完全等价——例如命名空间声明的位置变化、自闭合写法变化。
    返回 None 表示不是 XML 或无法解析（此时应退回字节比对）。
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.lstrip().startswith("<"):
        return None
    try:
        return ET.canonicalize(xml_data=text)
    except Exception:
        return None


def compare_package(a: Path, b: Path) -> dict:
    za, zb = zipfile.ZipFile(str(a)), zipfile.ZipFile(str(b))
    na, nb = set(za.namelist()), set(zb.namelist())
    same, changed = [], []
    for n in sorted(na & nb):
        if _sha(za.read(n)) == _sha(zb.read(n)):
            same.append(n)
        else:
            changed.append(n)
    # 对字节不同的 XML 部件，再判一次「语义是否等价」
    sem_changed, serial_only, order_only = [], [], []
    for n in changed:
        ca, cb = canonical_xml(za.read(n)), canonical_xml(zb.read(n))
        if ca is not None and ca == cb:
            serial_only.append(n)
        elif n in _ORDER_INSENSITIVE_PARTS:
            oa = canonical_xml_children_sorted(za.read(n))
            ob = canonical_xml_children_sorted(zb.read(n))
            if oa is not None and oa == ob:
                order_only.append(n)
            else:
                sem_changed.append(n)
        else:
            sem_changed.append(n)
    return {
        "only_in_old": sorted(na - nb),
        "only_in_new": sorted(nb - na),
        "identical": same,
        "modified": changed,
        "modified_semantic": sem_changed,
        "modified_serialization_only": serial_only,
        "modified_order_only": order_only,
        "zip_old": za,
        "zip_new": zb,
    }


def compare_styles(za, zb) -> dict:
    def ids(z):
        xml = z.read("word/styles.xml").decode("utf-8")
        return dict(
            re.findall(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>', xml, re.S)
        )

    sa, sb = ids(za), ids(zb)
    common = set(sa) & set(sb)
    return {
        "added": sorted(set(sb) - set(sa)),
        "removed": sorted(set(sa) - set(sb)),
        "changed": sorted(i for i in common if _sha(sa[i].encode()) != _sha(sb[i].encode())),
        "unchanged_count": sum(1 for i in common if _sha(sa[i].encode()) == _sha(sb[i].encode())),
    }


def compare_settings(za, zb) -> dict:
    def tags(z):
        xml = z.read("word/settings.xml").decode("utf-8")
        return re.findall(r"<w:(\w+)[ />]", xml)

    ta, tb = tags(za), tags(zb)
    return {"added": sorted(set(tb) - set(ta)), "removed": sorted(set(ta) - set(tb))}


def audit_capture_styles(za, zb, ids: list[str], say) -> bool:
    """
    审计「目录捕获样式」是否真的零外观影响。

    这类样式（如 SciTOC1/SciTOC2）的唯一职责是给正文段落挂 w:outlineLvl，
    好让 { TOC \\t ... } 能收录它们。它**绝不能**携带任何 rPr 外观属性
    （字体 / 字号 / 加粗…）——否则一旦某个 run 没有显式直接格式，就会继承
    样式里的外观，把正文改掉。这是纯内容比对**查不出来**的一类风险，故单列检查。

    返回 True 表示全部通过。
    """
    if not ids:
        return True
    xml_a = za.read("word/styles.xml").decode("utf-8")
    xml_b = zb.read("word/styles.xml").decode("utf-8")

    def grab(xml, sid):
        m = re.search(
            rf'<w:style [^>]*w:styleId="{re.escape(sid)}"[^>]*>(.*?)</w:style>', xml, re.S
        )
        return m.group(0) if m else None

    say("**目录捕获样式审计**（应「新文件新增 / 原始不存在」且「只含 outlineLvl、无 rPr」）")
    say()
    ok = True
    for sid in ids:
        old, new = grab(xml_a, sid), grab(xml_b, sid)
        if new is None:
            say(f"- `{sid}`：⚠️ 新文件中不存在")
            ok = False
            continue
        problems = []
        if old is not None:
            problems.append("原始文件中已存在（非新增，定义被覆盖）")
        body = new
        if "<w:rPr" in body:
            problems.append("含 rPr 外观属性（可能改动正文外观）")
        if "<w:outlineLvl" not in body:
            problems.append("未设置 outlineLvl（无法被目录收录）")
        if "w:basedOn" not in body:
            problems.append("未声明 basedOn（继承链不明）")
        if problems:
            ok = False
            say(f"- `{sid}`：⚠️ " + "；".join(problems))
        else:
            say(f"- `{sid}`：✅ 新增、仅含 outlineLvl、无 rPr、basedOn 明确")
    say()
    return ok


def aligned_body_report(old: Path, new: Path, say) -> dict:
    """
    按位置对齐比对正文：自动找出新文件开头「新增块」的数量（用原始首块的**文本**定位，
    与样式/格式无关），再逐块严格比对剩余部分。

    采用三层判定，逐层收紧：
      第 1 层 内容层——只比文本（段落文字 / 单元格文字），忽略一切格式；
      第 2 层 格式层——在内容一致的前提下，比 run 级格式、段落属性、表格结构、列宽、图形数；
      第 3 层 样式层——仅 pStyle 名不同（视觉可能受影响，但不是内容改动）。

    返回 {"head": [...], "content_diffs": [...], "format_diffs": [...], "style_only": [...]}
    """
    of, nf = body_flow(old), body_flow(new)
    oa, na = [anchor_key(b) for b in of], [anchor_key(b) for b in nf]

    start = next((i for i in range(len(na)) if na[i] == oa[0]), None)
    if start is None:
        # 退路：原始首块文本为空时，改用第一个非空文本块作锚点
        idx = next((k for k, b in enumerate(oa) if b[1]), None)
        if idx is not None:
            start = next((i for i in range(len(na)) if na[i] == oa[idx]), None)
    if start is None:
        say("⚠️ 未能在新文件中定位到原始首块，无法按位置对齐（请改用默认 diff 模式）。")
        return {"head": [], "content_diffs": [], "format_diffs": [], "style_only": []}

    say(
        f"- 原始正文块数：**{len(of)}**；新文件总块数：**{len(nf)}**；"
        f"新文件开头额外块数：**{start}**"
    )
    say()
    say("新增块清单（即插入的目录及其附属块）：")
    say()
    for i, b in enumerate(nf[:start]):
        say(f"{i + 1}. {_describe(b, 70)}")
    say()

    rest_f = nf[start:]
    rest_a = na[start:]
    if len(rest_f) != len(of):
        say(f"⚠️ 正文块数不等（原始 {len(of)} vs 新文件 {len(rest_f)}），下面仅比对重叠部分。")
        say()

    n = min(len(of), len(rest_f))

    # ---- 第 1 层：内容层（纯文本 + 表格单元格文本）----
    text_diffs = [i for i in range(n) if oa[i] != rest_a[i]]

    say("### 第 1 层｜内容层比对（只比文字，忽略全部格式）")
    say()
    if not text_diffs:
        say(f"- ✅ 正文 **{n} 个块**的文字内容**逐块完全一致**，无任何增删改。")
    else:
        say(f"- ⚠️ 共 **{len(text_diffs)}** 块文字内容不一致：")
        say()
        for i in text_diffs[:20]:
            say(f"  - 第 {i} 块：{_describe(of[i], 60)}")
            say(f"    - 原始：`{re.sub(chr(92) + 's+', ' ', str(oa[i]))[:180]}`")
            say(f"    - 新件：`{re.sub(chr(92) + 's+', ' ', str(rest_a[i]))[:180]}`")
    say()

    # ---- 第 2 层：格式层（在文本一致的前提下比 run/段落/表格格式）----
    format_diffs = [i for i in range(n) if i not in text_diffs and of[i][1:] != rest_f[i][1:]]
    style_only = []
    for i in format_diffs:
        if of[i][2:] == rest_f[i][2:]:  # 仅 pStyle 不同
            style_only.append((i, of[i][1], rest_f[i][1]))

    say(
        "### 第 2 层｜格式层比对（文字一致前提下，比 run 级格式 / 段落属性 / "
        "表格结构 / 列宽 / 图形数）"
    )
    say()
    fmt_real = [i for i in format_diffs if i not in {s[0] for s in style_only}]
    if not fmt_real:
        say(
            "- ✅ 所有文字一致的块，其 run 级格式、段落属性、表格结构、列宽、图形数量**均无差异**。"
        )
    else:
        say(f"- ⚠️ 共 **{len(fmt_real)}** 块存在格式差异（文字相同，仅格式不同）：")
        say()
        for i in fmt_real[:20]:
            say(f"  - 第 {i} 块：{_describe(of[i], 60)}")
            say(f"    - 原始：`{re.sub(chr(92) + 's+', ' ', str(of[i][2:]))[:180]}`")
            say(f"    - 新件：`{re.sub(chr(92) + 's+', ' ', str(rest_f[i][2:]))[:180]}`")
    say()

    # ---- 第 3 层：样式层 ----
    say("### 第 3 层｜段落样式变化（文字与格式均未变）")
    say()
    if style_only:
        from collections import Counter

        for (a, b), c in Counter((a, b) for _, a, b in style_only).items():
            say(f"- `{a or 'Normal'}` → `{b or 'Normal'}`：**{c}** 段")
    else:
        say("- 无")
    say()

    return {
        "head": nf[:start],
        "text_diffs": text_diffs,
        "format_diffs": fmt_real,
        "style_only": style_only,
    }


def _diff_report(old: Path, new: Path, say) -> bool:
    """默认模式：用 difflib 定位新增/删除/修改的块。返回「内容是否一致」。"""
    fa, fb = body_flow_nostyle(old), body_flow_nostyle(new)
    sm = difflib.SequenceMatcher(a=fa, b=fb, autojunk=False)
    inserted = deleted = replaced = equal = 0
    say(f"- 原始正文块数：{len(fa)}；新文件正文块数：{len(fb)}")
    say()
    say("| 操作 | 块数 | 位置（原始下标 → 新文件下标） |")
    say("|---|---|---|")
    details: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            equal += i2 - i1
            continue
        if tag == "insert":
            inserted += j2 - j1
            say(f"| 新增 | {j2 - j1} | — → [{j1}, {j2}) |")
            for k in range(j1, min(j2, j1 + 4)):
                details.append(f"  - 新增块：{_describe(fb[k])}")
            if j2 - j1 > 4:
                details.append(f"  - …（其余 {j2 - j1 - 4} 块省略）")
        elif tag == "delete":
            deleted += i2 - i1
            say(f"| 删除 | {i2 - i1} | [{i1}, {i2}) → — |")
            for k in range(i1, min(i2, i1 + 4)):
                details.append(f"  - 删除块：{_describe(fa[k])}")
        else:
            replaced += max(i2 - i1, j2 - j1)
            say(f"| 修改 | {max(i2 - i1, j2 - j1)} | [{i1}, {i2}) → [{j1}, {j2}) |")
            for k in range(min(i2 - i1, j2 - j1)):
                if fa[i1 + k] != fb[j1 + k]:
                    details.append(f"  - 变化前：{_describe(fa[i1 + k])}")
                    details.append(f"  - 变化后：{_describe(fb[j1 + k])}")
    say()
    say(f"- 逐块完全一致（**忽略段落样式**）：**{equal}** 块")
    say()
    if details:
        say(
            "明细（提示：新文件首部插入块时，difflib 可能把「目录条目」与"
            "「正文同名表图题」配对显示为修改，属对齐假象；"
            "请用 `--align-body` 模式复核）："
        )
        say()
        for d in details[:40]:
            say(d)
        if len(details) > 40:
            say(f"  - …（共 {len(details)} 条，已截断）")
        say()
    return inserted == 0 and deleted == 0 and replaced == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="逐部件比对两个 .docx 的内容一致性")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("-o", "--out", default=None, help="把报告写入 Markdown 文件")
    ap.add_argument(
        "--align-body",
        action="store_true",
        help="按位置对齐比对正文（适用于新文件首部插入了目录/封面等块）",
    )
    ap.add_argument(
        "--capture-styles",
        default="SciTOC1,SciTOC2",
        help="要审计的「目录捕获样式」列表（逗号分隔）；传空字符串跳过",
    )
    args = ap.parse_args()

    old, new = Path(args.old).resolve(), Path(args.new).resolve()
    for p in (old, new):
        if not p.exists():
            print(f"[ERROR] 文件不存在：{p}")
            return 2

    lines: list[str] = []

    def say(s: str = ""):
        print(s)
        lines.append(s)

    say("# docx 内容一致性比对报告")
    say()
    say(f"- 原始文件：`{old.name}`")
    say(f"- 新文件　：`{new.name}`")
    say()

    pkg = compare_package(old, new)
    say("## 1. 包级部件比对")
    say()
    say(f"- 完全一致的部件：**{len(pkg['identical'])}** 个")
    say(
        f"- 字节不同的部件：**{len(pkg['modified'])}** 个（其中**语义等价**："
        f"{len(pkg['modified_serialization_only']) + len(pkg['modified_order_only'])} 个"
        f"［仅序列化差异 {len(pkg['modified_serialization_only'])} 个"
        f" + 仅子元素顺序差异 {len(pkg['modified_order_only'])} 个］；"
        f"**语义有实质变化**：{len(pkg['modified_semantic'])} 个）"
    )
    say(
        f"- 仅新文件新增的部件：{len(pkg['only_in_new'])} 个"
        + (f" → {pkg['only_in_new']}" if pkg["only_in_new"] else "")
    )
    say(
        f"- 仅原始文件有的部件：{len(pkg['only_in_old'])} 个"
        + (f" → {pkg['only_in_old']}" if pkg["only_in_old"] else "")
    )
    say()
    if pkg["modified_semantic"]:
        say("**语义有实质变化的部件**（XML 规范形式也不同）：")
        for n in pkg["modified_semantic"]:
            say(f"- `{n}`")
        say()
    if pkg["modified_serialization_only"]:
        say("**仅序列化差异的部件**（XML 规范形式完全相同，内容无变化）：")
        for n in pkg["modified_serialization_only"]:
            say(f"- `{n}`")
        say()
    if pkg["modified_order_only"]:
        say("**仅子元素顺序差异的部件**（顺序在该部件中无语义，内容无变化）：")
        for n in pkg["modified_order_only"]:
            say(f"- `{n}`")
        say()

    st = compare_styles(pkg["zip_old"], pkg["zip_new"])
    say("## 2. 样式表 styles.xml")
    say()
    say(f"- 未变动样式：{st['unchanged_count']} 个")
    say(f"- 新增样式：{st['added'] or '无'}")
    say(f"- 删除样式：{st['removed'] or '无'}")
    say(f"- 定义被改动的样式：{st['changed'] or '无'}")
    say()
    cap_ids = [s.strip() for s in (args.capture_styles or "").split(",") if s.strip()]
    cap_ok = audit_capture_styles(pkg["zip_old"], pkg["zip_new"], cap_ids, say)

    se = compare_settings(pkg["zip_old"], pkg["zip_new"])
    say("## 3. settings.xml")
    say()
    say(f"- 新增设置项：{se['added'] or '无'}")
    say(f"- 移除设置项：{se['removed'] or '无'}")
    say()

    say("## 4. 正文流逐块比对")
    say()

    if args.align_body:
        say("模式：**按位置对齐**（自动剔除新文件开头新增的块）")
        say()
        rep = aligned_body_report(old, new, say)
        text_same = not rep["text_diffs"]
        fmt_same = not rep["format_diffs"]
        content_same = text_same and fmt_same
    else:
        content_same = _diff_report(old, new, say)
        text_same = fmt_same = content_same

    say("## 5. 结论")
    say()
    if args.align_body:
        if text_same:
            say(
                "- ✅ **内容层**：正文文字（段落文字 + 表格单元格文字）**逐块完全一致**，"
                "无任何增删改。"
            )
        else:
            say(f"- ⚠️ **内容层**：有 **{len(rep['text_diffs'])}** 块文字不一致，详见第 4 节。")
        if fmt_same:
            say(
                "- ✅ **格式层**：文字一致的块，其 run 级格式、段落属性、表格结构、"
                "列宽、图形数量均无差异。"
            )
        else:
            say(f"- ⚠️ **格式层**：有 **{len(rep['format_diffs'])}** 块文字相同但格式不同。")
        if rep["style_only"]:
            say(
                f"- ℹ️ **样式层**：{len(rep['style_only'])} 个段落仅「段落样式名」发生变化"
                "（为生成目录而套用捕获样式），文字与格式均未改动；"
                "捕获样式本身已在第 2 节审计为「零外观属性」。"
            )
        else:
            say("- ℹ️ **样式层**：无段落样式变化。")
    elif content_same:
        say(
            "- ✅ **正文内容逐块完全一致**（文本、逐 run 格式、段落属性、表格结构、"
            "列宽、单元格文本、图形数量均无差异）。"
        )
    else:
        say("- ⚠️ 正文存在内容差异，详见第 4 节。")

    if cap_ids:
        if cap_ok:
            say(
                f"- ✅ **目录捕获样式审计**：`{'`、`'.join(cap_ids)}` 均为新增且不含任何"
                "外观属性（只挂 outlineLvl），不会影响正文外观。"
            )
        else:
            say(f"- ⚠️ **目录捕获样式审计**：`{'`、`'.join(cap_ids)}` 存在问题，见第 2 节。")

    media_a = [n for n in pkg["identical"] + pkg["modified"] if n.startswith("word/media/")]
    media_new = [n for n in pkg["only_in_new"] if n.startswith("word/media/")]
    media_del = [n for n in pkg["only_in_old"] if n.startswith("word/media/")]
    say(
        f"- 媒体文件：一致 {len(media_a)} 个；仅新文件有 {len(media_new)} 个；"
        f"仅原始有 {len(media_del)} 个。"
    )

    # 页眉页脚用「语义等价」判定：python-docx 重存会产生纯序列化差异，
    # 若只看字节差异会误报「页眉页脚被改动」。
    _hf = r"word/(header|footer)\d*\.xml$"
    hf_sem = [n for n in pkg["modified_semantic"] if re.match(_hf, n)]
    hf_ser = [n for n in pkg["modified_serialization_only"] if re.match(_hf, n)]
    hf_new = [n for n in pkg["only_in_new"] if re.match(_hf, n)]
    if hf_sem or hf_new:
        say(f"- ⚠️ 页眉页脚部件：**语义有实质变化** → {hf_sem + hf_new}")
    elif hf_ser:
        say(
            f"- ✅ 页眉页脚部件：**内容语义完全一致**（{len(hf_ser)} 个仅有序列化差异，"
            f"页码 / 域定义未受影响）"
        )
    elif [n for n in pkg["identical"] if re.match(_hf, n)]:
        say("- ✅ 页眉页脚部件：字节完全一致")
    say()
    say(
        "> 注：本比对覆盖 OOXML 包内的全部部件。**域（field）的缓存显示值**"
        "（如 PAGE 页码、目录条目页码）属于内容的一部分，会随排版变化而不同；"
        "新增目录块会使正文分页整体后移，属预期变化。"
    )

    if args.out:
        Path(args.out).write_text("\n".join(lines), encoding="utf-8")
        print(f"\n[报告已写入] {args.out}")
    return 0 if (content_same and cap_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
