"""
TVAX-009 EOP2 面对面专家会议 PPT 优化脚本（最终版）

整合 8 项原始要求 + 5 项补充要求：
  1. 第 5 页 ④ 高危人群表述去歧义
  2. 第 7 页 改用"乙肝报告发病率"（非急性）数据、"几乎无人接种过疫苗"换稳妥表述
  3. 第 15/16 页之间新增页：本品 III 期 CpG 用量 vs 6 个已上市 CpG 产品
  4. 第 23/31 页 补充阳性对照（艾美诚信）说明
  5. 第 66 页 应急场景并入早保护，弱化表述
  6. 全文"持久性更好"类表述客观化（第 40、59 页；第 61 页按要求保留不动）
  7. 第 18 页后新增页：传统铝佐剂乙肝减针次研究证据（保留 3 项研究，去掉 PreHevbrio）
  8. 新增页版式：16:9 / 纯白 / 暗红 RGB(192,0,0)；参考文献置于页脚灰色字体

用法:
  python scripts/update_tvax009_eop2_ppt_final.py
"""

from __future__ import annotations

import contextlib
import copy
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Inches

# ---------------------------------------------------------------- 路径 / 常量
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "review_materials" / "TVAX-009 EOP2 面对面专家会议-20260910 GJ-LL.pptx"
OUT = ROOT / "review_materials" / "TVAX-009 EOP2 面对面专家会议-20260910 GJ-LL_optimized.pptx"

EMU_IN = 914400
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
XMLNS = 'xmlns:p="{}" xmlns:a="{}" xmlns:r="{}"'.format(NS["p"], NS["a"], NS["r"])

RED = "C00000"  # 品牌暗红 RGB(192,0,0)
GRAY = "7A808A"  # 参考文献灰
WHITE = "FFFFFF"
BLACK = "000000"
YAHEI = "微软雅黑"
ARIAL = "Arial"

LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


def inches(v: float) -> int:
    return int(round(v * EMU_IN))


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- 形状工具
def find_shape(slide, name=None, contains=None, left_in=None, top_in=None):
    hits = []
    for shp in slide.shapes:
        if name is not None and shp.name != name:
            continue
        if contains is not None:
            if not shp.has_text_frame or contains not in shp.text_frame.text:
                continue
        if left_in is not None:
            if shp.left is None or abs(shp.left / EMU_IN - left_in) > 0.02:
                continue
        if top_in is not None:
            if shp.top is None or abs(shp.top / EMU_IN - top_in) > 0.02:
                continue
        hits.append(shp)
    return hits


def rewrite_paragraph(p, segments, keep_lead=0, template_index=0):
    """按片段重写段落，公式化保留原 run 的字体格式。

    segments     : [(text, bold)]，bold 为 None 表示沿用模板 run 的加粗设置
    keep_lead    : 保留前 N 个 run 原样不动（用于保留"● xxx："之类的前导样式）
    template_index: 取第 N 个 run 的 rPr 作为新 run 的格式模板
    """
    runs = list(p.runs)
    if not runs:
        r = p.add_run()
        r.text = segments[0][0]
        runs = list(p.runs)

    tpl = runs[min(template_index, len(runs) - 1)]._r.find("{{{}}}rPr".format(NS["a"]))
    tpl = copy.deepcopy(tpl) if tpl is not None else None

    for r in runs[keep_lead:]:
        r._r.getparent().remove(r._r)

    for text, bold in segments:
        r = p.add_run()
        r.text = text
        if tpl is not None:
            r._r.insert(0, copy.deepcopy(tpl))
        if bold is not None:
            r.font.bold = bold
    return p


def set_para_text(p, text):
    return rewrite_paragraph(p, [(text, None)], keep_lead=0, template_index=0)


def set_cell_text(cell, text) -> None:
    """单元格：保留首个 run 的格式，替换文字，清理多余段落。

    文本内可含 ``\\n`` 自动拆为多段，每段单独 ``<a:p>``，沿用首个 run 的
    ``rPr`` 模板（含字体 / 字号 / 颜色 / 加粗）与该段的 ``pPr``（行距 / 对齐）。
    """
    if text is None:
        return
    parts = str(text).split("\n")
    tf = cell.text_frame
    paras = tf.paragraphs
    if not paras:
        return

    # 在调用 set_para_text 改写首个 paragraph 的 runs 之前，先把 rPr 模板抽出来
    src_p = paras[0]._p
    template_rPr = None
    if paras[0].runs:
        rpr = paras[0].runs[0]._r.find(qn("a:rPr"))
        if rpr is not None:
            template_rPr = copy.deepcopy(rpr)

    set_para_text(paras[0], parts[0])

    # 清理原有第二段起的 paragraphs（多段追加时会重建）
    for extra in paras[1:]:
        extra._p.getparent().remove(extra._p)

    if len(parts) == 1:
        return

    # 追加后续段：克隆当前 src_p（已携带首段的 pPr），移除其中所有 run，
    # 重新挂上"行文本 + rPr 副本"。
    # 注意 OOXML 中 <a:p> 的子元素顺序为 (a:pPr?, (a:r|a:br|a:fld)*, a:endParaRPr?)，
    # a:endParaRPr 必须排在最后；若把新 <a:r> 直接 append 到它之后，XML 非法，
    # PowerPoint 会静默丢弃该 run（表现为该段文字不渲染），故这里必须 insert
    # 到 a:endParaRPr 之前。
    txBody = src_p.getparent()
    for line in parts[1:]:
        new_p = copy.deepcopy(src_p)
        for r in new_p.findall(qn("a:r")):
            new_p.remove(r)
        r_xml = '<a:r xmlns:a="{}">'.format(NS["a"])
        if template_rPr is not None:
            r_xml += etree.tostring(template_rPr, encoding="unicode")
        r_xml += f"<a:t>{esc(line)}</a:t></a:r>"
        new_r = etree.fromstring(r_xml)
        end_rpr = new_p.find(qn("a:endParaRPr"))
        if end_rpr is not None:
            end_rpr.addprevious(new_r)  # 保持 endParaRPr 位于末尾
        else:
            new_p.append(new_r)
        txBody.append(new_p)


def next_shape_id(slide, start: int = 200) -> int:
    ids = []
    for el in slide.shapes._spTree.iter():
        if el.tag.endswith("}cNvPr") and el.get("id"):
            with contextlib.suppress(ValueError):
                ids.append(int(el.get("id")))
    return max(ids) + 1 if ids else start


def clone_shape(src_shape, dest_slide):
    """深拷贝形状（含全部格式）到目标页，保证视觉与母版一致。"""
    el = copy.deepcopy(src_shape._element)
    dest_slide.shapes._spTree.append(el)
    new = dest_slide.shapes[-1]
    c_nv = el.find(".//p:cNvPr", NS)
    if c_nv is not None:
        c_nv.set("id", str(next_shape_id(dest_slide)))
    return new


def move_slide(prs, old_index: int, new_index: int) -> None:
    lst = prs.slides._sldIdLst
    el = list(lst)[old_index]
    lst.remove(el)
    lst.insert(new_index, el)


def get_layout(prs, name="Blank"):
    for lay in prs.slide_layouts:
        if lay.name == name:
            return lay
    return prs.slide_layouts[6]


# ---------------------------------------------------------------- XML 构造
def _rpr(sz, bold, color, latin=YAHEI, ea=YAHEI, cs="+mn-cs", kern=True):
    b = ' b="1"' if bold else ' b="0"'
    k = ' kern="1200"' if kern else ""
    cs_xml = f'<a:cs typeface="{cs}"/>' if cs else ""
    return (
        f'<a:rPr sz="{sz}"{b} i="0"{k} dirty="0">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="{latin}" pitchFamily="34" charset="0"/>'
        f'<a:ea typeface="{ea}" pitchFamily="34" charset="-122"/>{cs_xml}</a:rPr>'
    )


def para_xml(runs, align="l", line_pct=100000) -> str:
    """runs: [(text, sz, bold, color[, latin[, ea]])]"""
    r_xml = "".join(
        f"<a:r>{_rpr(r[1], r[2], r[3], r[4] if len(r) > 4 else YAHEI, r[5] if len(r) > 5 else YAHEI)}"
        f"<a:t>{esc(r[0])}</a:t></a:r>"
        for r in runs
    )
    a = {"l": "l", "ctr": "ctr", "r": "r"}[align]
    return (
        f'<a:p><a:pPr marL="0" algn="{a}" defTabSz="457200" rtl="0" eaLnBrk="1" '
        f'latinLnBrk="0" hangingPunct="1">'
        f'<a:lnSpc><a:spcPct val="{line_pct}"/></a:lnSpc>'
        f'<a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft>'
        f"</a:pPr>{r_xml}</a:p>"
    )


def hdr_cell_xml(text, align="l") -> str:
    """表头单元格：暗红底 + 白色加粗 11pt 微软雅黑（复刻母版样式）。"""
    a = {"l": "l", "ctr": "ctr"}[align]
    return (
        "<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:pPr algn="{a}"><a:lnSpc><a:spcPct val="95000"/></a:lnSpc>'
        '<a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft></a:pPr>'
        '<a:r><a:rPr sz="1100" b="1" i="0" dirty="0">'
        f'<a:solidFill><a:srgbClr val="{WHITE}"/></a:solidFill>'
        f'<a:latin typeface="{YAHEI}" pitchFamily="34" charset="-122"/>'
        f'<a:ea typeface="{YAHEI}" pitchFamily="34" charset="-122"/></a:rPr>'
        f"<a:t>{esc(text)}</a:t></a:r></a:p></a:txBody>"
        '<a:tcPr marL="27432" marR="27432" marT="13716" marB="13716" anchor="ctr">'
        f'<a:solidFill><a:srgbClr val="{RED}"/></a:solidFill></a:tcPr></a:tc>'
    )


def body_cell_xml(text, align="l", bold=False, sz=1100, color=BLACK) -> str:
    """表体单元格：白底 + 黑色正文（复刻母版样式）。"""
    a = {"l": "l", "ctr": "ctr"}[align]
    b = ' b="1"' if bold else ' b="0"'
    return (
        "<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>"
        '<a:p><a:pPr marL="0" algn="%s" defTabSz="457200" rtl="0" eaLnBrk="1" '
        'latinLnBrk="0" hangingPunct="1">'
        '<a:lnSpc><a:spcPct val="115000"/></a:lnSpc>'
        '<a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft></a:pPr>'
        '<a:r><a:rPr sz="%d"%s i="0" kern="1200" dirty="0">'
        '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
        '<a:latin typeface="%s" pitchFamily="34" charset="-122"/>'
        '<a:ea typeface="%s" pitchFamily="34" charset="-122"/><a:cs typeface="+mn-cs"/></a:rPr>'
        "<a:t>%s</a:t></a:r></a:p></a:txBody>"
        '<a:tcPr marL="27432" marR="27432" marT="13716" marB="13716" anchor="ctr">'
        '<a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:tcPr></a:tc>'
        % (a, sz, b, color, YAHEI, YAHEI, esc(text), WHITE)
    )


def add_table(
    slide,
    left_in,
    top_in,
    col_widths_in,
    header,
    rows,
    row_h_in=0.50,
    header_h_in=0.42,
    align_map=None,
    highlight_last=False,
):
    col_emu = [inches(w) for w in col_widths_in]
    total_w = sum(col_emu)
    total_h = inches(header_h_in + row_h_in * len(rows))
    grid = "".join(f'<a:gridCol w="{w}"/>' for w in col_emu)
    aligns = align_map or ["l"] * len(col_widths_in)

    trs = [
        '<a:tr h="%d">%s</a:tr>'
        % (inches(header_h_in), "".join(hdr_cell_xml(h, aligns[i]) for i, h in enumerate(header)))
    ]
    for r_i, row in enumerate(rows):
        is_hl = highlight_last and r_i == len(rows) - 1
        trs.append(
            '<a:tr h="%d">%s</a:tr>'
            % (
                inches(row_h_in),
                "".join(
                    body_cell_xml(v, align=aligns[c_i], bold=is_hl, color=RED if is_hl else BLACK)
                    for c_i, v in enumerate(row)
                ),
            )
        )

    xml = (
        f"<p:graphicFrame {XMLNS}>"
        "<p:nvGraphicFramePr>"
        f'<p:cNvPr id="{next_shape_id(slide)}" name="Table 5"/>'
        '<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>'
        "<p:nvPr/></p:nvGraphicFramePr>"
        f'<p:xfrm><a:off x="{inches(left_in)}" y="{inches(top_in)}"/>'
        f'<a:ext cx="{total_w}" cy="{total_h}"/></p:xfrm>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
        '<a:tbl><a:tblPr firstRow="1" bandRow="1">'
        "<a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr>"
        f"<a:tblGrid>{grid}</a:tblGrid>{''.join(trs)}</a:tbl>"
        "</a:graphicData></a:graphic></p:graphicFrame>"
    )
    slide.shapes._spTree.append(etree.fromstring(xml.encode("utf-8")))
    return slide.shapes[-1]


def add_textbox(slide, left_in, top_in, width_in, height_in, paras, name="TextBox 20"):
    """paras: [ runs, ... ]，每个 runs 为 para_xml 的 run 元组列表。"""
    body = "".join(para_xml(pr) for pr in paras)
    xml = (
        f"<p:sp {XMLNS}>"
        "<p:nvSpPr>"
        f'<p:cNvPr id="{next_shape_id(slide)}" name="{name}"/>'
        '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{inches(left_in)}" y="{inches(top_in)}"/>'
        f'<a:ext cx="{inches(width_in)}" cy="{inches(height_in)}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t">'
        f"<a:noAutofit/></a:bodyPr><a:lstStyle/>{body}</p:txBody></p:sp>"
    )
    slide.shapes._spTree.append(etree.fromstring(xml.encode("utf-8")))
    return slide.shapes[-1]


def add_note(slide, left_in, top_in, width_in, height_in, text, sz=1100):
    return add_textbox(
        slide,
        left_in,
        top_in,
        width_in,
        height_in,
        [[("注：", sz, True, RED), (text, sz, False, BLACK)]],
        name="TextBox 30",
    )


def add_refs(slide, left_in, top_in, width_in, height_in, text):
    """页脚参考文献：8.5pt 灰色 Arial。"""
    return add_textbox(
        slide,
        left_in,
        top_in,
        width_in,
        height_in,
        [[(text, 850, False, GRAY, ARIAL, YAHEI)]],
        name="TextBox 19",
    )


# ---------------------------------------------------------------- 主流程
def main() -> int:
    if not SRC.exists():
        print(f"[ERROR] 找不到源文件: {SRC}")
        return 1

    prs = Presentation(str(SRC))
    log(f"源文件 : {SRC.name}")
    log(f"原页数 : {len(list(prs.slides))}")

    # ========================================================== 要求 1：第 5 页
    s5 = prs.slides[4]
    box5 = find_shape(s5, name="文本框 1")[0]
    set_para_text(
        box5.text_frame.paragraphs[6],
        "       " + "④高危人群新发感染率高：男性感染率高于女性，未接种乙肝疫苗者、"
        "合并糖尿病或肾功能不全者、以及生活在南方或欠发达地区的人群",
    )
    log("[要求1] 第 5 页 ④ 高危人群表述已按用户给定文案更新为去歧义表述")

    # ========================================================== 要求 2：第 7 页
    s7 = prs.slides[6]
    sub_right = [s for s in find_shape(s7, name="TextBox 4") if s.left / EMU_IN > 5][0]
    set_para_text(
        sub_right.text_frame.paragraphs[0], "国内外监测系统报告：≥60 岁人群乙肝报告发病率"
    )
    sub_left = [s for s in find_shape(s7, name="TextBox 4") if s.left / EMU_IN < 5][0]
    set_para_text(
        sub_left.text_frame.paragraphs[0], "国内外监测系统报告：18-59 岁人群乙肝报告发病率"
    )
    # 源文件中 "≥60 岁" 小标题被错放在 "18-59 岁核心结论" 上方（原 L=5.231/T=1.076），
    # 移回其所属的 ≥60 岁表格（L=0.525/T=3.544）正上方，并统一列宽避免溢出。
    sub_left.left, sub_left.top = Inches(0.550), Inches(1.074)
    sub_left.width, sub_left.height = Inches(4.600), Inches(0.265)
    sub_right.left, sub_right.top = Inches(0.525), Inches(3.225)
    sub_right.width, sub_right.height = Inches(4.600), Inches(0.301)
    log("[要求2] 第 7 页 ≥60 岁小标题已从右上角移回 ≥60 岁表格上方（消除原有错位）")

    tables = find_shape(s7, name="Table 5")
    gframe_t60 = [t for t in tables if t.left / EMU_IN < 0.54][0]  # 保留对图框的引用，便于重定位
    gframe_t1859 = [t for t in tables if t.left / EMU_IN >= 0.54][0]
    t60 = gframe_t60.table
    t1859 = gframe_t1859.table

    set_cell_text(t60.cell(0, 1), "≥60 岁人群乙肝报告发病率（/10 万）")
    # 数据来源：① 中国公共卫生 2004—2017 趋势分析；② CDC Viral Hepatitis Surveillance 2023；
    # ③ ECDC Hepatitis B AER 2022。ECDC 为分年龄段（急性＋慢性）通报率，
    # 由本页欧洲图逐条像素测量还原（标定：基线=0.00，32.5 px = 1.00 单位）。
    for i, (a, b) in enumerate(
        [
            ("中国（全国法定传染病报告系统，2004–2017 年均）", "163.11（全乙肝）"),
            ("美国（CDC 病毒性肝炎监测，2023）", "6.6（急性 0.7＋慢性 5.9）"),
            # 显式分为两段（而非让 PowerPoint 自然折行），避免出现 "≥65 岁" / "3.7" 的孤字行；
            # 两段各 1 行，行数不变，故不影响任何几何。
            ("欧洲 ECDC（EU/EEA 通报率，2022，急性＋慢性）", "55–64 岁 5.8\n≥65 岁 3.7"),
        ],
        start=1,
    ):
        set_cell_text(t60.cell(i, 0), a)
        set_cell_text(t60.cell(i, 1), b)

    set_cell_text(t1859.cell(0, 1), "18-59 岁人群乙肝报告发病率（/10 万）")
    for i, (a, b) in enumerate(
        [
            # 显式分段，避免 "40–" / "59 岁 181.62" 这种在数字中间断行的排版瑕疵
            ("中国（全国法定传染病报告系统，2004–2017 年均）", "20–39 岁 211.00\n40–59 岁 181.62"),
            # 4 个年龄段各占 1 行（而非两两成段让 PowerPoint 自然折行），
            # 避免 "…30–39 岁" / "10.7" 的孤字行；总行数仍为 4 行 → 行高 0.718" 不变
            (
                "美国（CDC 病毒性肝炎监测，2023）",
                "20–29 岁 5.2\n30–39 岁 10.7\n40–49 岁 12.8（最高）\n50–59 岁 10.7",
            ),
            ("欧洲 ECDC（EU/EEA 通报率，2022，急性＋慢性）", "25–54 岁 6.3–9.7"),
        ],
        start=1,
    ):
        set_cell_text(t1859.cell(i, 0), a)
        set_cell_text(t1859.cell(i, 1), b)

    # ----- 第 7 页布局回流（整页重排）-----
    # 推导依据（页面 13.333" × 7.5"；正文 11pt 微软雅黑、行距 95%、单元格上下边距 0.015"）：
    #   · 实测单行文本占高 = 0.172"（由本页 ≥60 表 4 行 × 0.420" 精准反推），
    #     故单元格行高 = 0.030" + n × 0.172"。
    #   · 18-59 表"美国 CDC"行写入 4 个年龄段后为 2 段 × 2 行 = 4 行文本，
    #     该行高度 = 0.030 + 4×0.172 = 0.718"（原 0.420"）；整表视觉高
    #     0.415 + 0.420 + 0.718 + 0.420 = 1.973"（原 1.675"，增长 0.298"）。
    #   · ≥60 表每格最多 2 行文本（0.374" < 0.420"），行高不增长，整表 1.680"。
    #     实测其视觉底 = T + 1.680"，故来源行必须整体让到该底之下。
    #   · 底部三图原高 2.015~2.033"，按 0.95 等比微缩至 1.915~1.932"
    #     （6.5% 的视觉差异不可辨），以腾出安全间距。
    # 重排后自上而下 5 处间距统一 0.030"，页面底边距 0.050"，全部元素互不重叠。
    geo = {
        "sub_left_top": 1.000,  # 18-59 小标题（原 1.074；上移后距分隔线 0.975 留 0.025"）
        "t1859_top": 1.295,  # 18-59 表（原 1.536）
        "sub_right_top": 3.298,  # ≥60 小标题（原 3.225；现与 18-59 表视觉底 3.268 留 0.030"）
        "t60_top": 3.629,  # ≥60 表（原 3.544）
        "refs_top": 5.339,  # 来源行（原 5.148；现与 ≥60 表视觉底 5.309 留 0.030"）
        "charts_top": 5.519,  # 底部三图（原 5.344；与来源行底 5.489 留 0.030"）
        "chart_scale": 0.95,  # 三图等比缩放
        "rbox1859_top": 1.383,  # 右侧 18-59 结论框（原 1.624；随表同步位移 -0.241"）
        "rtxt1859_top": 1.436,  # 右侧 18-59 结论文字（原 1.677）
        "rbox60_top": 3.593,  # 右侧 ≥60 结论框（原 3.508；随表同步位移 +0.085"）
        "rtxt60_top": 3.608,  # 右侧 ≥60 结论文字（原 3.523）
    }
    sub_left.top = Inches(geo["sub_left_top"])
    gframe_t1859.top = Inches(geo["t1859_top"])
    sub_right.top = Inches(geo["sub_right_top"])
    gframe_t60.top = Inches(geo["t60_top"])
    # 右侧两个结论框（Rectangle 6）+ 其正文（TextBox 7）随对应表格同步位移，保持原有相对关系
    for rbox in find_shape(s7, name="Rectangle 6"):
        rbox.top = Inches(geo["rbox60_top"] if rbox.top / EMU_IN > 3 else geo["rbox1859_top"])
    for rtxt in find_shape(s7, name="TextBox 7"):
        rtxt.top = Inches(geo["rtxt60_top"] if rtxt.top / EMU_IN > 3 else geo["rtxt1859_top"])
    # 底部三图（图片 30 / 31 / 32）等比微缩并整体下移
    for pic in s7.shapes:
        if pic.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            pic.width = int(pic.width * geo["chart_scale"])
            pic.height = int(pic.height * geo["chart_scale"])
            pic.top = Inches(geo["charts_top"])

    # 灰色字体标注本页三组数据来源（置于 ≥60 岁结论框与底部三图之间的空白带）
    add_refs(
        s7,
        0.525,
        geo["refs_top"],
        12.450,
        0.150,
        "数据来源：① 中国公共卫生, 2022（中国大陆居民乙肝发病趋势分析）；"
        "② CDC. Viral Hepatitis Surveillance Report—United States, 2023；"
        "③ ECDC. Hepatitis B—Annual Epidemiological Report 2022。",
    )
    log(
        '[要求2.2] 第 7 页已整页重排：18-59 表 "美国 CDC" 行 4 行文本致表高 +0.298"，'
        '下方链条（≥60 小标题 / ≥60 表 / 来源行 / 底部三图）已按 0.030" 统一间距重排，'
        "右侧结论框同步位移，底部三图等比缩至 95%"
    )

    concl = find_shape(s7, name="TextBox 7")
    c60 = [c for c in concl if c.top / EMU_IN > 3][0]
    c1859 = [c for c in concl if c.top / EMU_IN <= 3][0]

    tf = c60.text_frame
    set_para_text(
        tf.paragraphs[0],
        "核心结论：我国儿童及青少年乙肝报告发病率随乙肝疫苗免疫规划实施持续下降，"
        "而 ≥60 岁人群乙肝报告发病率总体呈上升趋势。",
    )
    rewrite_paragraph(
        tf.paragraphs[1],
        [
            (
                "该人群多出生于乙肝疫苗纳入免疫规划（1992 年）之前，既往乙肝疫苗接种覆盖率低、"
                "缺乏疫苗诱导的免疫记忆，属 HBV 易感人群。《中国公共卫生》2022 年流行病学分析显示，"
                "2004—2017 年我国 ≥60 岁居民乙肝年均报告发病率达 ",
                False,
            ),
            ("163.11/10 万", True),
            ("，明显高于同期全人群水平，提示老年人是乙肝防控需重点关注的人群之一。", False),
        ],
    )

    tf = c1859.text_frame
    set_para_text(
        tf.paragraphs[0],
        "核心结论：18‑59 岁成人是我国乃至全球乙肝报告病例的主要构成人群，"
        "该年龄段报告发病率整体呈持续下降趋势，但仍是病例占比最高的人群。",
    )
    set_para_text(
        tf.paragraphs[1],
        "34 岁及以上群体出生于 1992 年（乙肝免疫规划实施）之前，"
        "新生儿乙肝疫苗接种未覆盖此部分人群，且成人疫苗接种覆盖率整体偏低；",
    )
    set_para_text(
        tf.paragraphs[2],
        "疫苗使少年儿童乙肝发病显著减少，疾病负担转移至成年人，成年人是乙肝防控的重点人群[3]",
    )
    log("[要求2] 第 7 页 数据口径改为乙肝报告发病率；已删除原老年人群绝对化表述；结论重写")

    # ========================================================== 要求 4：第 23/31 页
    PC_NOTE = (
        "阳性对照为艾美诚信生产的重组乙型肝炎疫苗（汉逊酵母），其 HBsAg 含量同样为 20 μg/0.5 mL，"
        "表达体系亦为汉逊酵母（Hansenula polymorpha），与本试验疫苗在抗原剂量与表达体系上具有可比性。"
    )
    add_note(prs.slides[22], 0.428, 6.99, 12.60, 0.42, PC_NOTE)
    add_note(prs.slides[30], 0.669, 6.88, 11.38, 0.42, PC_NOTE)
    log("[要求4] 第 23、31 页已补充阳性对照（艾美诚信）说明文字")

    # ========================================================== 要求 6：持久性表述
    s40 = prs.slides[39]
    set_para_text(
        find_shape(s40, name="文本框 1")[0].text_frame.paragraphs[2],
        "高抗体水平比例至 M12 维持较高水平，更长期持久性有待 M24/M36 数据确认；",
    )
    log("[要求6] 第 40 页 持久性表述已客观化")

    s59 = prs.slides[58]
    set_para_text(
        find_shape(s59, name="文本框 1")[0].text_frame.paragraphs[0],
        "免疫原性：本产品起效早，抗-HBs 阳转率高；M12 维持较高水平，持久性待随访确认",
    )
    set_para_text(
        find_shape(s59, name="文本框 7")[0].text_frame.paragraphs[0],
        "相对于对照疫苗 3 针免疫程序，本疫苗可提前 5 个月获得免疫保护；"
        "至 M12 阳转率维持较高水平，更长期持久性有待随访数据确认；",
    )
    log("[要求6] 第 59 页两处持久性表述已客观化（第 61 页按要求保留原文不动）")

    # ========================================================== 要求 5：第 66 页
    s66 = prs.slides[65]
    tb9 = find_shape(s66, name="TextBox 9")[0]
    rewrite_paragraph(
        tb9.text_frame.paragraphs[0],
        [
            (
                "1 针后（M1）高剂量组阳转率即高于对照（54.86%/43.92% vs 31.76%，"
                "P<0.0001/P=0.0310）；2 针后达 97.89%-100.00%，亦可用于应急接种",
                None,
            )
        ],
        keep_lead=1,
        template_index=1,
    )
    tb9.top = Inches(4.915)
    for nm in ("Rectangle 13", "Rectangle 14", "TextBox 15"):
        for shp in find_shape(s66, name=nm):
            shp._element.getparent().remove(shp._element)
    log("[要求5] 第 66 页 应急场景已并入早保护表述；独立“应急场景”卡片已移除")

    # ========================================================== 要求 3 / 7：新增页
    blank = get_layout(prs, "Blank")
    ref_bar = find_shape(prs.slides[14], name="Rectangle 1")[0]
    ref_sep = find_shape(prs.slides[14], name="Rectangle 3")[0]
    ref_title = find_shape(prs.slides[14], name="TextBox 2")[0]
    ref_sub = find_shape(prs.slides[14], name="TextBox 4")[0]
    ref_concl = sorted(find_shape(prs.slides[6], name="Rectangle 6"), key=lambda s: s.left)[-1]

    def build_slide(
        title,
        subtitle,
        col_w,
        header,
        rows,
        align_map,
        table_top,
        table_row_h,
        concl_text,
        ref_text,
        highlight_last=False,
        concl_top=5.10,
    ):
        s = prs.slides.add_slide(blank)
        for shp in list(s.shapes):
            if shp.is_placeholder:
                shp._element.getparent().remove(shp._element)
        clone_shape(ref_bar, s)  # 品牌色竖条
        t = clone_shape(ref_title, s)  # 标题
        clone_shape(ref_sep, s)  # 分隔线
        sub = clone_shape(ref_sub, s)  # 副标题
        set_para_text(t.text_frame.paragraphs[0], title)
        set_para_text(sub.text_frame.paragraphs[0], subtitle)

        add_table(
            s,
            0.45,
            table_top,
            col_w,
            header,
            rows,
            row_h_in=table_row_h,
            align_map=align_map,
            highlight_last=highlight_last,
        )

        c_box = clone_shape(ref_concl, s)  # 结论底框
        c_box.left, c_box.top = Inches(0.45), Inches(concl_top)
        c_box.width, c_box.height = Inches(12.45), Inches(1.20)
        add_textbox(s, 0.62, concl_top + 0.06, 12.11, 1.08, [concl_text], name="TextBox 7")
        add_refs(s, 0.45, concl_top + 1.32, 12.45, 0.62, ref_text)
        return s

    # ---------- 新增页 B：传统铝佐剂减针次证据（后插到第 18 页之后）
    B_TITLE = "传统铝佐剂乙肝疫苗减针次（2 剂 / 1 剂）程序的研究证据"
    B_SUB = "现有研究一致提示：传统铝佐剂疫苗减少针次后，抗体水平衰减更快、长期血清保护率更低"
    B_HEADER = ["研究", "设计 / 人群", "免疫程序", "关键结果"]
    B_ROWS = [
        [
            "Wang ZZ, et al. Vaccine 2016（PMID: 26801063）",
            "中国健康成人 18–25 岁，n=353，随机对照（NCT02203357）",
            "20 μg（0-1-6 月）3 剂 vs 60 μg 2 剂（0-1 月 / 0-2 月）",
            "2 剂组全程后血清保护率 93.64%–99.19%，与 3 剂组（100%）无显著差异；"
            "但 M12 抗-HBs GMC 2 剂组仅 256.30 / 235.15 mIU/mL，"
            "显著低于 3 剂组的 1,456.63 mIU/mL（P<0.001），提示减针次后抗体衰减更快",
        ],
        [
            "Wang ZZ, et al. 2 年随访（PMID: 29420134）",
            "同一队列 M24 随访（n=59 / 45 / 55）",
            "同上",
            "M24 血清保护率：3 剂组 98.31% vs 2 剂组 88.37%（0-1 月）、85.19%（0-2 月）（P=0.014）；"
            "GMC 427.46 vs 89.74 / 89.80 mIU/mL（P<0.01）；研究者建议成人优先采用标准 3 剂程序",
        ],
        [
            "Oelschlager KA, et al. Mil Med 2023（PMID: 36525511）",
            "决策分析模型，基于 23,004 名美国新兵真实世界数据",
            "铝佐剂 HepB 2 剂 vs CpG 佐剂 HepB 2 剂",
            "接种 2 剂后，铝佐剂组预期仅 24% 达到保护水平，CpG 佐剂组为 92%；"
            "在第 2–3 剂之间约 5 个月间隔期内，76% 人群处于无保护状态",
        ],
    ]
    B_CONCL = [
        ("结论：", 1300, True, BLACK),
        (
            "现有研究一致提示，传统铝佐剂乙肝疫苗减少针次（2 剂）虽可提高接种完成率，"
            "但抗体水平衰减更快、长期血清保护率显著低于标准 3 剂程序（M24：85.19%–88.37% vs 98.31%），"
            "且第 2 剂后存在明显保护缺口（仅 24% 达保护水平）。提示单纯减少传统铝佐剂疫苗的针次"
            "难以满足长期保护需求，需通过佐剂技术升级（如 CpG 佐剂联合铝佐剂）予以弥补。",
            1300,
            False,
            BLACK,
        ),
    ]
    B_REF = (
        "参考文献：[1] Wang ZZ, Li MQ, Wang P, et al. Comparative immunogenicity of hepatitis B vaccine "
        "with different dosages and schedules in healthy young adults in China. Vaccine. 2016;34(8):1034-1039. "
        "（PMID: 26801063）　[2] Wang ZZ, et al. Comparison of immunogenicity between hepatitis B vaccines "
        "with different dosages and schedules among healthy young adults in China: a 2-year follow-up study. "
        "（PMID: 29420134）　[3] Oelschlager KA, Termini MS, Stevenson C. Preventing hepatitis B virus "
        "infection among U.S. military personnel: potential impact of a 2-dose versus 3-dose vaccine on "
        "medical readiness. Mil Med. 2023;188(7-8):e2067-e2073.（PMID: 36525511）"
    )

    build_slide(
        B_TITLE,
        B_SUB,
        [2.35, 2.55, 2.85, 4.70],
        B_HEADER,
        B_ROWS,
        ["l", "l", "l", "l"],
        table_top=1.32,
        table_row_h=1.15,
        concl_text=B_CONCL,
        ref_text=B_REF,
        concl_top=5.45,
    )
    move_slide(prs, len(list(prs.slides)) - 1, 18)
    log("[要求7] 新增页（传统铝佐剂减针次证据，3 项研究）已插入为第 19 页")

    # ---------- 新增页 A：CpG 用量对比（插到第 15 / 16 页之间）
    A_TITLE = "试验疫苗与已上市 CpG 佐剂疫苗的 CpG 用量比较"
    A_SUB = "本品拟定 III 期 CpG-QCX1 剂量（1,000 μg）与 6 个已上市含 CpG 佐剂产品的用量对比"
    A_HEADER = [
        "产品（企业）",
        "适应症",
        "上市状态",
        "CpG 佐剂类型",
        "CpG 用量",
        "抗原 / 佐剂组成",
        "装量",
    ]
    A_ROWS = [
        [
            "HEPLISAV-B（Dynavax）",
            "乙型肝炎",
            "FDA 批准上市（2017）",
            "CpG 1018",
            "3,000 μg",
            "HBsAg 20 μg（汉逊酵母）",
            "0.5 mL",
        ],
        [
            "CYFENDUS（Emergent）",
            "炭疽",
            "FDA 批准上市（2023）",
            "CpG 7909",
            "250 μg",
            "AVA 抗原＋铝佐剂",
            "0.5 mL",
        ],
        [
            "SCB-2019（三叶草生物）",
            "COVID-19",
            "中国 EUA（2022）",
            "CpG 1018",
            "1,500 μg",
            "重组 S 三聚体＋铝佐剂 750 μg",
            "0.5 mL",
        ],
        [
            "MVC-COV1901（高端疫苗）",
            "COVID-19",
            "中国台湾地区 EUA",
            "CpG 1018",
            "750 μg",
            "重组 S-2P＋Al(OH)₃ 375 μg",
            "0.5 mL",
        ],
        [
            "IndoVac（Bio Farma）",
            "COVID-19",
            "印尼 EUA（2022）",
            "CpG 1018",
            "750 μg",
            "重组 RBD＋铝佐剂 750 μg",
            "0.5 mL",
        ],
        [
            "CORBEVAX（Biological E）",
            "COVID-19",
            "印度 EUA（2021）",
            "CpG 1018",
            "750 μg",
            "重组 RBD＋铝佐剂 750 μg",
            "0.5 mL",
        ],
        [
            "TVAX-009（远大赛威信）",
            "乙型肝炎",
            "EOP2（拟定 III 期）",
            "CpG-QCX1",
            "1,000 μg",
            "HBsAg 20 μg（汉逊酵母）＋铝佐剂",
            "0.5 mL",
        ],
    ]
    A_CONCL = [
        ("结论：", 1300, True, BLACK),
        (
            "已上市含 CpG 佐剂产品的 CpG 用量区间为 250–3,000 μg。本品拟定 III 期 CpG-QCX1 剂量为 1,000 μg，"
            "仅为同适应症已上市产品 HEPLISAV-B（CpG 1018 3,000 μg）的约 1/3，亦低于 SCB-2019（1,500 μg）；"
            "结合本品 CpG 与铝佐剂联合使用的设计，在保障免疫应答的前提下，本品选择了相对保守的 CpG 用量。",
            1300,
            False,
            BLACK,
        ),
    ]
    A_REF = (
        "参考文献：[1] HEPLISAV-B（HepB-CpG）FDA Package Insert & Clinical Review, 2017.　"
        "[2] CYFENDUS（AV7909）FDA Package Insert, 2023.　"
        "[3] Richmond P, et al. Lancet. 2021;397(10275):682-694.（SCB-2019）　"
        "[4] Hsieh SM, et al. Lancet Respir Med. 2021;9(12):1396-1406.（MVC-COV1901）　"
        "[5] IndoVac（Bio Farma）印尼 BPOM EUA, 2022.　"
        "[6] CORBEVAX（Biological E）印度 DCGI EUA, 2021.　"
        "[7] 本品 III 期临床试验方案（TVAX-009）"
    )

    build_slide(
        A_TITLE,
        A_SUB,
        [2.45, 1.15, 1.75, 1.20, 1.05, 3.95, 0.90],
        A_HEADER,
        A_ROWS,
        ["l", "ctr", "ctr", "ctr", "ctr", "l", "ctr"],
        table_top=1.30,
        table_row_h=0.47,
        concl_text=A_CONCL,
        ref_text=A_REF,
        highlight_last=True,
        concl_top=5.10,
    )
    move_slide(prs, len(list(prs.slides)) - 1, 15)
    log("[要求3] 新增页（CpG 用量对比）已插入为第 16 页（原第 15 / 16 页之间）")

    prs.save(str(OUT))
    log(f"总页数 : {len(list(prs.slides))}")
    log(f"输出   : {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
