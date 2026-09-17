#!/usr/bin/env python
"""
add_toc_field_to_docx.py

为「全文未使用内置标题样式」的 Word 报告插入**可自动更新页码**的目录（TOC 域）。

适用范围
--------
review_materials/新建文件夹/ 下的
《远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅱ期-免后12个月补充分析》
全文所有段落均为 Normal 样式、无任何内置标题样式、无现成目录，
因此无法直接用 { TOC \\o "1-3" } 抓取条目。

实现方案（外观零改动 + 页码自动准确 + 打开即见）
----------------------------------------------
1. 新建两个「目录捕获样式」SciTOC1 / SciTOC2（basedOn Normal，**只**带
   w:outlineLvl，不写任何 rPr / pPr 外观属性），分别套用到「小节标题」
   「表题 / 图题」段落。原段落本就无 pStyle（继承默认 Normal），因此套用后
   **外观零变化**；outlineLvl 只影响目录收录与导航窗格，不影响渲染。
2. 归一化 TOC 1 / TOC 2 样式：
   **重点**——本文档 styles.xml 中遗留了旧的 `toc 1`（含 <w:caps/>）与 `toc 2`
   （含 <w:smallCaps/>）样式定义，若不清理，目录条目会被渲染成全大写 / 小型大写，
   与正文文字不一致（正文为 "抗-HBs"，目录会变成 "抗-HBS"）。此处显式清除大小写转换，
   并去掉 rFonts 上的主题字体绑定。
3. 在 TOC 1 / TOC 2 样式中定义「右对齐 + 点线前导符」制表位，保证页码对齐美观
   （制表位位置按页面可用宽度自动计算）。
4. 在正文最前插入目录标题 + 复杂域 { TOC \\t "SciTOC1,1,SciTOC2,2" \\h \\z } + 分页符；
   域的 begin/instrText/separate 并入首个条目段落、end 并入末个条目段落（与 Word
   自身生成的段落结构一致，不产生多余空段）。
5. 在 settings.xml 写入 <w:updateFields w:val="true"/>，打开文档时自动更新域。
6. **（--embed-page-numbers）用 Word COM 把真实页码写回域的缓存结果**，
   使目录在打开时即已完整显示（含页码）；域仍然保留，页码可随时更新。
7. 默认**另存为副本**（源文件名 + "_带目录.docx"），原文件不改动。

用法
----
    python add_toc_field_to_docx.py                       # 使用内置默认路径
    python add_toc_field_to_docx.py "<源文件.docx>"
    python add_toc_field_to_docx.py "<源文件.docx>" -o "<输出文件.docx>"
    python add_toc_field_to_docx.py "<源文件.docx>" --embed-page-numbers
    python add_toc_field_to_docx.py "<源文件.docx>" --in-place          # 原地修改（慎用）
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import (
    WD_ALIGN_PARAGRAPH,
    WD_BREAK,
    WD_TAB_ALIGNMENT,
    WD_TAB_LEADER,
)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Pt

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import contextlib

from edit_office_utils import make_run  # noqa: E402  项目内复用：统一 run 构建

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

DEFAULT_SRC = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\新建文件夹"
    r"\远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅱ期-免后12个月补充分析"
    r"_V1.0_20260403(0911).docx"
)

OUTPUT_SUFFIX = "_带目录"

RE_SECTION = re.compile(r"^14\.2\.5\.\d+[\s\u3000]")  # 小节标题：14.2.5.5 免后抗-HBs_18-59岁人群
RE_TABLE_CAP = re.compile(r"^表\s*14\.2\.5\.")  # 表题：表14.2.5.5.1 ……
RE_FIGURE_CAP = re.compile(r"^图\s*14\.2\.5\.")  # 图题：图14.2.5.5.1 ……

SECTION_STYLE = "SciTOC1"  # 小节标题 → 目录 1 级
CAPTION_STYLE = "SciTOC2"  # 表题 / 图题 → 目录 2 级

TOC_STYLE_IDS = {0: "TOC1", 1: "TOC2"}  # 大纲级别 → TOC 样式 styleId

TOC_FIELD_INSTR = ' TOC \\t "SciTOC1,1,SciTOC2,2" \\h \\z '
TOC_PLACEHOLDER = (
    "目录将在打开文档时自动更新；若此处仍显示本提示，"
    "请右键选择「更新域」→「更新整个目录」（或按 F9）。"
)

TOC_TITLE = "目　　录"
TOC_TITLE_SPACE_AFTER = 12  # pt

# 目录条目版式（(字号pt, 加粗, 段前pt, 段后pt, 左缩进pt)）；本文档条目多且图题很长，
# 需收紧段间距才能让 26 条目录压在 1 页内（原为 6/6 + 2/2 时会溢出到第 2 页）。
TOC_ENTRY_FORMAT = {
    0: (12.0, True, 5.0, 5.0, 0.0),  # 小节标题
    1: (10.5, False, 0.0, 0.0, 14.0),  # 表题 / 图题
}

# 需要从 TOC 样式上清除的遗留属性（会改变目录条目文字外观）
_RPR_STRIP = ("w:caps", "w:smallCaps", "w:vanish")
_STYLE_STRIP = (
    "w:autoRedefine",
    "w:unhideWhenUsed",
    "w:semiHidden",
    "w:qFormat",
    "w:locked",
)


# --------------------------------------------------------------------------- #
# 底层工具
# --------------------------------------------------------------------------- #


def _set_outline_level(style, level: int) -> None:
    """给样式写入 w:outlineLvl（决定 TOC 层级），按 CT_PPr 的 schema 顺序插入。"""
    pPr = style.element.get_or_add_pPr()
    el = pPr.find(qn("w:outlineLvl"))
    if el is None:
        el = OxmlElement("w:outlineLvl")
        ref = None
        for tag in ("w:rPr", "w:sectPr", "w:pPrChange"):
            ref = pPr.find(qn(tag))
            if ref is not None:
                break
        if ref is not None:
            ref.addprevious(el)
        else:
            pPr.append(el)
    el.set(qn("w:val"), str(level))


def _style_key(name: str) -> str:
    """样式名归一化：去空格 + 转小写（Word 内置名如 "toc 1" 与 "TOC 1" 等价）。"""
    return (name or "").replace(" ", "").lower()


def find_existing_style(document, name: str):
    """
    大小写/空格不敏感地查找既有样式（先比 styleId，再比 name）。

    必要性：python-docx 的 styles["TOC 1"] 是**大小写精确**匹配，而 Word 内置
    样式在 styles.xml 中的名字是小写 "toc 1"。若直接 add_style，会生成与既有
    样式 **styleId 重复**的新样式（两个 w:styleId="TOC1"），Word 解析时取用前者
    （即原始定义，可能带 w:caps），导致目录条目被渲染成全大写。
    """
    key = _style_key(name)
    for st in document.styles:
        if _style_key(getattr(st, "style_id", "")) == key:
            return st
        if _style_key(getattr(st, "name", "")) == key:
            return st
    return None


def _ensure_paragraph_style(document, name: str):
    """取得（或新建）一个段落样式；优先复用既有样式，避免 styleId 重复。"""
    existing = find_existing_style(document, name)
    if existing is not None:
        return existing
    return document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)


def _reset_style_body(style) -> None:
    """清空样式的 pPr / rPr 与遗留行为标记，保留 styleId / name / basedOn。"""
    el = style.element
    for tag in ("w:pPr", "w:rPr", *_STYLE_STRIP):
        for e in el.findall(qn(tag)):
            el.remove(e)


def _strip_case_transform(style) -> list[str]:
    """清除样式上遗留的大小写转换（w:caps / w:smallCaps），返回被清除的属性名。"""
    removed: list[str] = []
    rPr = style.element.get_or_add_rPr()
    for tag in _RPR_STRIP:
        for e in rPr.findall(qn(tag)):
            rPr.remove(e)
            removed.append(tag.split(":")[1])
    # 同时清掉 rFonts 上的主题字体绑定，避免中文字体被主题西文字体顶替
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is not None:
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rFonts.get(qn(attr)) is not None:
                del rFonts.attrib[qn(attr)]
    return removed


def _make_toc_capture_style(document, name: str, level: int):
    """
    目录捕获样式：基于 Normal，**只**挂 w:outlineLvl，不写任何 rPr / pPr 外观属性。

    设计要点（务必保持）：
    - 该样式只是「让 Word 能把这段正文收进目录」的标记，绝不是用来改外观的；
    - 因此绝不能写 font.name / font.size / font.bold 之类，否则一旦正文某个 run
      没有显式 rPr（直接格式），就会继承样式里的字体/字号/加粗，把正文外观改掉；
    - 原段落本来就没有 pStyle（继承默认的 Normal），所以 basedOn Normal + 仅加
      outlineLvl ⇒ 视觉上零变化。outlineLvl 只影响导航窗格 / 目录收录，不影响渲染。
    """
    style = _ensure_paragraph_style(document, name)
    _reset_style_body(style)
    style.base_style = document.styles["Normal"]
    _set_outline_level(style, level)
    # 断言：捕获样式不得残留任何 rPr 外观属性
    rPr = style.element.find(qn("w:rPr"))
    if rPr is not None:
        for child in list(rPr):
            rPr.remove(child)
    return style


def _make_toc_entry_style(
    document,
    name: str,
    size_pt: float,
    bold: bool,
    tab_twips: int,
    left_indent_pt: float,
    space_before: float,
    space_after: float,
):
    """目录条目样式：清遗留 caps，设定字体/缩进/点线右制表位。"""
    style = _ensure_paragraph_style(document, name)
    removed = _strip_case_transform(style)
    for tag in _STYLE_STRIP:
        for e in style.element.findall(qn(tag)):
            style.element.remove(e)
    if style.element.find(qn("w:basedOn")) is None:
        style.base_style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(size_pt)
    style.font.bold = bold

    pf = style.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.0
    if left_indent_pt:
        pf.left_indent = Pt(left_indent_pt)
    pf.tab_stops.add_tab_stop(Emu(int(tab_twips) * 635), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    return style, removed


def _get_settings_element(document):
    """兼容不同 python-docx 版本地取出 settings.xml 根元素。"""
    try:
        return document.settings.element
    except Exception:
        pass
    for part in document.part.package.iter_parts():
        if str(part.partname).endswith("/settings.xml"):
            return getattr(part, "element", None) or getattr(part, "_element", None)
    return None


# ----------------------------- 域（field）构造 ----------------------------- #


def _text_run(text: str):
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def _tab_run():
    r = OxmlElement("w:r")
    r.append(OxmlElement("w:tab"))
    return r


def _fldchar_run(kind: str, dirty: bool = False):
    r = OxmlElement("w:r")
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), kind)
    if dirty:
        fc.set(qn("w:dirty"), "true")
    r.append(fc)
    return r


def _instr_run(instr: str):
    r = OxmlElement("w:r")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r.append(it)
    return r


def _entry_content_runs(text: str, page):
    """条目正文：标题文本 + 制表符 + 页码。"""
    return [_text_run(text), _tab_run(), _text_run("" if page is None else str(page))]


def _entry_paragraph(level: int, text: str, page=None, head: bool = False, tail: bool = False):
    """构造一个目录条目段落，可同时承载域的 begin（head）或 end（tail）。"""
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    ps = OxmlElement("w:pStyle")
    ps.set(qn("w:val"), TOC_STYLE_IDS.get(level, "TOC2"))
    pPr.append(ps)
    p.append(pPr)
    if head:
        p.append(_fldchar_run("begin", dirty=True))
        p.append(_instr_run(TOC_FIELD_INSTR))
        p.append(_fldchar_run("separate"))
    for r in _entry_content_runs(text, page):
        p.append(r)
    if tail:
        p.append(_fldchar_run("end"))
    return p


def _build_toc_field(entries):
    """
    构造 TOC 域（与 Word 自身生成的段落结构一致，不产生多余空段）：
        begin + instrText + separate 置于**首个条目段落开头**；
        end 置于**末个条目段落结尾**。
    entries: [(level, text, page_or_None), ...]；为空时写提示文本。
    """
    if not entries:
        p = OxmlElement("w:p")
        p.append(_fldchar_run("begin", dirty=True))
        p.append(_instr_run(TOC_FIELD_INSTR))
        p.append(_fldchar_run("separate"))
        p.append(_text_run(TOC_PLACEHOLDER))
        p.append(_fldchar_run("end"))
        return [p]

    n = len(entries)
    return [
        _entry_paragraph(level, text, page, head=(i == 0), tail=(i == n - 1))
        for i, (level, text, page) in enumerate(entries)
    ]


def _find_toc_field(document):
    """
    用 fldChar 状态机精确定位 TOC 域：
    返回 (begin_paragraph, end_paragraph, first_result_paragraph_after_begin)。
    """
    body = document.element.body
    begin_p = end_p = None
    for p in (c for c in body.iterchildren() if c.tag == qn("w:p")):
        if begin_p is None:
            has_begin = any(
                fc.get(qn("w:fldCharType")) == "begin" for fc in p.iter(qn("w:fldChar"))
            )
            if has_begin and any("TOC" in (e.text or "") for e in p.iter(qn("w:instrText"))):
                begin_p = p
        if begin_p is not None and end_p is None:
            if any(fc.get(qn("w:fldCharType")) == "end" for fc in p.iter(qn("w:fldChar"))):
                end_p = p
                break
    if begin_p is None:
        raise RuntimeError("未找到 TOC 域")
    return begin_p, end_p


def _clear_field_head(begin_p) -> None:
    """保留 begin_p 中 pPr 及 begin/instrText/separate 三个 run，删除其余内容。"""
    seen_sep = False
    for child in list(begin_p):
        if child.tag == qn("w:pPr"):
            continue
        if child.tag == qn("w:r") and not seen_sep:
            kinds = [fc.get(qn("w:fldCharType")) for fc in child.iter(qn("w:fldChar"))]
            if "separate" in kinds:
                seen_sep = True
            continue
        begin_p.remove(child)


def _set_update_fields(docx_path: Path) -> bool:
    """写入 <w:updateFields w:val="true"/>，打开文档时自动更新域。"""
    document = docx.Document(str(docx_path))
    settings = _get_settings_element(document)
    if settings is None:
        return False
    if settings.find(qn("w:updateFields")) is not None:
        return True
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    ref = None
    for tag in (
        "w:hdrShapeDefaults",
        "w:compat",
        "w:rsids",
        "w:themeFontLang",
        "w:shapeDefaults",
        "w:decimalSymbol",
        "w:listSeparator",
    ):
        ref = settings.find(qn(tag))
        if ref is not None:
            break
    if ref is not None:
        ref.addprevious(el)
    else:
        settings.append(el)
    document.save(str(docx_path))
    return True


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #


def _iter_body_blocks(document):
    """按正文顺序产出顶层 (kind, obj)：kind ∈ {'p', 'tbl'}（不下钻表格内部）。"""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield "p", Paragraph(child, document)
        elif tag == "tbl":
            yield "tbl", Table(child, document)


def _collect_entries(document) -> list[tuple[int, str]]:
    """按正文顺序识别目录条目：小节标题 = 0 级，表题 / 图题 = 1 级。"""
    out: list[tuple[int, str]] = []
    for kind, obj in _iter_body_blocks(document):
        if kind != "p":
            continue
        text = obj.text.strip()
        if not text:
            continue
        if RE_TABLE_CAP.match(text) or RE_FIGURE_CAP.match(text):
            out.append((1, text))
        elif RE_SECTION.match(text):
            out.append((0, text))
    return out


def mark_and_build(src: Path, dst: Path) -> dict:
    """第一步：套用捕获样式 + 插入 TOC 域（页码留空，待 Word 回填）。"""
    document = docx.Document(str(src))

    sec_style = _make_toc_capture_style(document, SECTION_STYLE, 0)
    cap_style = _make_toc_capture_style(document, CAPTION_STYLE, 1)

    sec = document.sections[0]
    usable = int(sec.page_width) - int(sec.left_margin) - int(sec.right_margin)
    tab_twips = round(usable / 635)

    def _entry_style(name: str, key: int):
        size_pt, bold, sb, sa, ind = TOC_ENTRY_FORMAT[key]
        return _make_toc_entry_style(document, name, size_pt, bold, tab_twips, ind, sb, sa)

    _, removed1 = _entry_style("TOC 1", 0)
    _, removed2 = _entry_style("TOC 2", 1)

    # --- 识别并标记正文标题 / 表图题 ---------------------------------------
    entries: list[tuple[int, str]] = []
    head_p = None
    for kind, obj in _iter_body_blocks(document):
        if kind != "p":
            continue
        if head_p is None:
            head_p = obj
        text = obj.text.strip()
        if not text:
            continue
        if RE_TABLE_CAP.match(text) or RE_FIGURE_CAP.match(text):
            obj.style = cap_style
            entries.append((1, text))
        elif RE_SECTION.match(text):
            obj.style = sec_style
            entries.append((0, text))

    # --- 插入「目录」标题 + TOC 域 + 分页符 --------------------------------
    anchor = head_p._p
    pPr = anchor.find(qn("w:pPr"))
    first_has_pbb = pPr is not None and pPr.find(qn("w:pageBreakBefore")) is not None

    p_title = document.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(TOC_TITLE_SPACE_AFTER)
    make_run(p_title, TOC_TITLE, bold=True, font_name="Times New Roman", font_size=Pt(16))

    tail = [p_title._p, *_build_toc_field([(lv, tx, None) for lv, tx in entries])]
    if not first_has_pbb:
        p_break = document.add_paragraph()
        p_break.paragraph_format.space_before = Pt(0)
        p_break.paragraph_format.space_after = Pt(0)
        p_break.add_run().add_break(WD_BREAK.PAGE)
        tail.append(p_break._p)

    for el in tail:  # 依次插到原首段之前，保持顺序
        anchor.addprevious(el)

    dst.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(dst))

    return {
        "src": str(src),
        "dst": str(dst),
        "entries": entries,
        "tab_twips": tab_twips,
        "stripped_case": {"TOC 1": removed1, "TOC 2": removed2},
        "page_break_added": not first_has_pbb,
    }


# --------------------------- Word 页码采集与回填 --------------------------- #


def collect_page_numbers(docx_path: Path, work_dir: Path) -> list[int]:
    """用 Word COM 更新目录域，按顺序返回每个条目的真实页码。"""
    import win32com.client as win32

    work_dir.mkdir(parents=True, exist_ok=True)
    # 必须转成绝对路径：Word 解析相对路径时以其自身 CWD 为基准，
    # 传相对路径会报「很抱歉，找不到您的文件」。
    tmp = (work_dir / "_pagemap_copy.docx").resolve()
    shutil.copy2(docx_path, tmp)
    word = doc = None
    try:
        word = win32.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(str(tmp), ConfirmConversions=False, AddToRecentFiles=False)
        for i in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(i).Update()
        doc.Fields.Update()
        pages: list[int] = []
        for par in doc.TablesOfContents(1).Range.Paragraphs:
            txt = par.Range.Text.strip().rstrip("\r")
            if not txt:
                continue
            m = re.search(r"(\d+)\s*$", txt.replace("\t", " "))
            if m:
                pages.append(int(m.group(1)))
        return pages
    finally:
        try:
            if doc is not None:
                doc.Close(0)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass
        with contextlib.suppress(Exception):
            tmp.unlink(missing_ok=True)


def embed_page_numbers(docx_path: Path, pages: list[int]) -> int:
    """把真实页码写入 TOC 域的缓存结果（域保留，仍可更新）。"""
    document = docx.Document(str(docx_path))
    body = document.element.body
    begin_p, end_p = _find_toc_field(document)

    # 删除旧的域结果段落（begin_p 之后、end_p 及其之前）
    if end_p is not None and end_p is not begin_p:
        cur = begin_p.getnext()
        while cur is not None and cur.tag == qn("w:p"):
            nxt = cur.getnext()
            body.remove(cur)
            if cur is end_p:
                break
            cur = nxt
    _clear_field_head(begin_p)

    entries = _collect_entries(document)
    if len(entries) != len(pages):
        raise RuntimeError(f"条目数不匹配：正文识别 {len(entries)} 条，Word 返回 {len(pages)} 条")
    if not entries:
        raise RuntimeError("正文未识别到任何目录条目")

    anchor = begin_p
    for i, (level, text) in enumerate(entries):
        if i == 0:  # 首条：内容追加在域头之后
            for r in _entry_content_runs(text, pages[i]):
                anchor.append(r)
            if len(entries) == 1:
                anchor.append(_fldchar_run("end"))
        else:
            p = _entry_paragraph(level, text, pages[i], tail=(i == len(entries) - 1))
            anchor.addnext(p)
            anchor = p

    document.save(str(docx_path))
    return len(entries)


# --------------------------------------------------------------------------- #


def verify(dst: Path) -> None:
    d = docx.Document(str(dst))
    print("\n===== 产物自检 =====")
    print(f"文件：{dst}")
    print(f"段落数={len(d.paragraphs)}  表格数={len(d.tables)}")
    print("updateFields 已启用：", _has_update_fields(d))
    from docx.text.paragraph import Paragraph

    shown = 0
    for child in d.element.body.iterchildren():
        if child.tag.split("}")[-1] != "p":
            continue
        par = Paragraph(child, d)
        print(f"  [{par.style.name:<8s}] {par.text.strip()[:66]}")
        shown += 1
        if shown >= 7:
            break
    n1 = sum(1 for p in d.paragraphs if p.style.name == SECTION_STYLE)
    n2 = sum(1 for p in d.paragraphs if p.style.name == CAPTION_STYLE)
    print(f"\n正文中套用捕获样式的段落：1 级 {n1} 条 + 2 级 {n2} 条 = {n1 + n2} 条")


def _has_update_fields(document) -> bool:
    s = _get_settings_element(document)
    return bool(s is not None and s.find(qn("w:updateFields")) is not None)


def main() -> int:
    ap = argparse.ArgumentParser(description="为 Word 文档插入可自动更新的目录（TOC 域）")
    ap.add_argument("src", nargs="?", default=str(DEFAULT_SRC), help="源 .docx 路径")
    ap.add_argument("-o", "--output", default=None, help="输出 .docx 路径")
    ap.add_argument("--in-place", action="store_true", help="原地修改源文件（慎用）")
    ap.add_argument(
        "--embed-page-numbers",
        action="store_true",
        help="用 Word COM 采集真实页码并写入域缓存结果（打开即见目录）",
    )
    ap.add_argument("--work-dir", default=None, help="COM 采集页码时使用的临时目录")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not src.exists():
        print(f"[ERROR] 源文件不存在：{src}")
        return 2

    if args.in_place:
        dst = src
    elif args.output:
        dst = Path(args.output).resolve()
    else:
        dst = src.with_name(f"{src.stem}{OUTPUT_SUFFIX}{src.suffix}")

    info = mark_and_build(src, dst)
    auto_update = _set_update_fields(dst)

    print("===== 执行结果 =====")
    print(f"源文件        ：{info['src']}")
    print(f"输出文件      ：{info['dst']}")
    print(f"已清除的大小写转换：{info['stripped_case']}")
    print(f"目录页码制表位：{info['tab_twips']} twips（右对齐点线）")
    print(f"自动更新域    ：{'已写入' if auto_update else '写入失败'}")
    print(f"目录后分页符  ：{'已插入' if info['page_break_added'] else '未插入'}")
    n1 = sum(1 for lv, _ in info["entries"] if lv == 0)
    n2 = len(info["entries"]) - n1
    print(f"目录条目      ：1 级 {n1} 条 + 2 级 {n2} 条 = {len(info['entries'])} 条")

    if args.embed_page_numbers:
        work = Path(args.work_dir).resolve() if args.work_dir else dst.parent / "_toc_verify"
        pages = collect_page_numbers(dst, work)
        n = embed_page_numbers(dst, pages)
        print(f"\n页码回填      ：已写入 {n} 条（页码范围 {min(pages)} ~ {max(pages)}）")

    verify(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
