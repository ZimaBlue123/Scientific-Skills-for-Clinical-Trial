#!/usr/bin/env python3
"""Build the deck "TVAX-009 Phase-1 cellular immunity vs CpG-adjuvanted HepB vaccines".

The visual identity (palette, Arial typography, 13.33x7.5in canvas, header rule,
section-divider layout) is cloned from:
    review_materials/TVAX-009 EOP2 面对面专家会议-20260911.pptx

Sources of the scientific content:
    review_materials/临床/远大赛威信...Ⅰ期-临床研究总结报告-V1.0-20250618.docx
    review_materials/文献库-F2F Meeting/02_同类产品-CpG佐剂与对照疫苗/...  (23 files)
    review_materials/文献库-F2F Meeting/.../HEPLISAV-B Dynavax/新增-细胞免疫补充（2026-09-15）/
        EMA_EPAR-Public-Assessment-Report-HEPLISAV-B.pdf
        PMID 18700037_CpG7909-Engerix-B_HIV_antigen-specific-CMI_LPR.pdf
        Ahodantin2026_HEPLISAV-B_AAV-HBV-mouse_CD4-CD40L_bioRxiv.pdf
        NCT04843852_BOOST-9_HEPLISAV-B_chronic-HBV_clinicaltrial-record.pdf
        NCT05727267_TherVacB_HEPLISAV-B-arm_clinicaltrial-record.pdf

Usage:
    python generate_ppt_ph1_cellular_vs_cpg_hepB.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
REF_PPTX = ROOT / "review_materials" / "TVAX-009 EOP2 面对面专家会议-20260911.pptx"
OUT_DIR = ROOT / "review_materials" / "汇报准备输出"
OUT_PPTX = OUT_DIR / "TVAX-009_Ⅰ期细胞免疫与同类CpG佐剂乙肝疫苗对比分析.pptx"
OLD_PPTX = OUT_DIR / "TVAX-009_Ⅰ期细胞免疫与HEPLISAV-B对比分析.pptx"

# ----------------------------------------------------------------------------
# visual identity cloned from the reference deck
# ----------------------------------------------------------------------------
RED = "C00000"  # primary accent (bars, numerals)
RED_DARK = "A11C1D"  # banner fill
PINK_LINE = "E3B8B8"  # hairline rule
PINK_PANEL = "FBEAEA"  # zebra row / side panel
BLACK = "000000"
GREY = "595F6B"
FOOTER_GREY = "B08888"
WHITE = "FFFFFF"
BORDER = "D9D9D9"
FONT = "Arial"

# --- vertical rhythm (standard, loosened) -----------------------------------
TITLE_TOP, TITLE_H = 0.12, 0.50  # page title
SUB_TOP, SUB_H = 0.64, 0.28  # page subtitle  (0.02in gap below title)
RULE_TOP = 0.94  # hairline rule  (0.02in gap below subtitle)
BODY_TOP = 1.08  # first content element
LINESPACE = 1.15  # paragraph line spacing
GAP = 7.0  # default space_after (pt)

FOOTER_TEXT = "TVAX-009 Ⅰ期细胞免疫与同类 CpG 佐剂乙肝疫苗对比分析"


# ----------------------------------------------------------------------------
# low level helpers
# ----------------------------------------------------------------------------
def _ea_font(run, name: str = FONT) -> None:
    """Mirror the latin typeface into the east-asian / complex-script slots."""
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = parse_xml(
                f'<a:{tag.split(":")[1]} xmlns:a="http://schemas.openxmlformats.org/'
                f'drawingml/2006/main" typeface="{name}"/>'
            )
            rPr.append(el)
        else:
            el.set("typeface", name)


def style_run(run, size=12, bold=False, color=BLACK, name=FONT, italic=False):
    f = run.font
    f.name = name
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = RGBColor.from_string(color)
    _ea_font(run, name)
    return run


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP, wrap=True):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return box


def put(
    tf,
    lines,
    size=12,
    bold=False,
    color=BLACK,
    align=PP_ALIGN.LEFT,
    space_after=GAP,
    line_spacing=LINESPACE,
    first=False,
):
    """`lines` may be a str or a list of (text, {overrides}) tuples."""
    if isinstance(lines, str):
        lines = [lines]
    for i, item in enumerate(lines):
        overrides = {}
        if isinstance(item, (tuple, list)):
            text, overrides = item[0], (item[1] if len(item) > 1 else {})
        else:
            text = item
        para = tf.paragraphs[0] if (first and i == 0) else tf.add_paragraph()
        para.alignment = overrides.get("align", align)
        sa = overrides.get("space_after", space_after)
        if sa is not None:
            para.space_after = Pt(sa)
        ls = overrides.get("line_spacing", line_spacing)
        if ls:
            para.line_spacing = ls
        if overrides.get("bullet"):
            para.text = ""
            r = para.add_run()
            r.text = "· "
            style_run(
                r,
                size=overrides.get("size", size),
                bold=True,
                color=overrides.get("bullet_color", RED),
            )
            r2 = para.add_run()
            r2.text = text
            style_run(
                r2,
                size=overrides.get("size", size),
                bold=overrides.get("bold", bold),
                color=overrides.get("color", color),
            )
        else:
            r = para.add_run()
            r.text = text
            style_run(
                r,
                size=overrides.get("size", size),
                bold=overrides.get("bold", bold),
                color=overrides.get("color", color),
                italic=overrides.get("italic", False),
            )
    return tf


def rect(slide, l, t, w, h, fill=RED, shape=MSO_SHAPE.RECTANGLE, line=None):
    sh = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = RGBColor.from_string(line)
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    sh.text_frame.word_wrap = True
    return sh


# ----------------------------------------------------------------------------
# table helpers
# ----------------------------------------------------------------------------
def _cell_border(cell, color=BORDER, width=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = tcPr.find(qn(tag))
        if ln is None:
            ln = parse_xml(
                f'<a:{tag.split(":")[1]} xmlns:a="http://schemas.openxmlformats.org/'
                f'drawingml/2006/main" w="{int(width * 12700)}" cap="flat" '
                f'cmpd="sng" algn="ctr"/>'
            )
            tcPr.append(ln)
        fill = ln.find(qn("a:solidFill"))
        if fill is None:
            fill = parse_xml(
                '<a:solidFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>'
            )
            ln.append(fill)
        else:
            for c in list(fill):
                fill.remove(c)
        fill.append(
            parse_xml(
                f'<a:srgbClr xmlns:a="http://schemas.openxmlformats.org/'
                f'drawingml/2006/main" val="{color}"/>'
            )
        )


def make_table(
    slide,
    l,
    t,
    w,
    rows,
    col_widths=None,
    row_h=0.32,
    header_h=0.40,
    fsize=10.0,
    hsize=10.5,
    header_fill=RED_DARK,
    header_color=WHITE,
    zebra=True,
    body_color=BLACK,
    aligns=None,
    bold_rows=(),
    red_cells=(),
    row_heights=None,
):
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    shp = slide.shapes.add_table(
        n_rows, n_cols, Inches(l), Inches(t), Inches(w), Inches(row_h * n_rows)
    )
    table = shp.table
    # turn off the theme's automatic banding so our own fills win
    tblPr = table._tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")

    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            table.columns[i].width = Emu(int(Inches(w) * cw / total))
    for i in range(n_rows):
        rh = row_heights[i] if row_heights else (header_h if i == 0 else row_h)
        table.rows[i].height = Inches(rh)

    aligns = aligns or {}
    for ri, row in enumerate(rows):
        for ci in range(n_cols):
            cell = table.cell(ri, ci)
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            _cell_border(cell)
            if ri == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(header_fill)
            elif zebra and ri % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(PINK_PANEL)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(WHITE)
            txt = row[ci] if ci < len(row) else ""
            tf = cell.text_frame
            tf.word_wrap = True
            para = tf.paragraphs[0]
            para.alignment = aligns.get(ci, PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            para.line_spacing = 1.10
            if (ri, ci) in red_cells:
                para.alignment = PP_ALIGN.CENTER
            r = para.add_run()
            r.text = txt
            bold = (ri == 0) or (ri in bold_rows)
            color = header_color if ri == 0 else body_color
            if (ri, ci) in red_cells:
                color = RED
                bold = True
            style_run(r, size=hsize if ri == 0 else fsize, bold=bold, color=color)
    return shp


# ----------------------------------------------------------------------------
# page furniture
# ----------------------------------------------------------------------------
def content_page(prs, layout, title, subtitle=None, page=None):
    slide = prs.slides.add_slide(layout)
    rect(slide, 0.25, 0.15, 0.09, 0.44, RED)
    box = textbox(slide, 0.46, TITLE_TOP, 12.40, TITLE_H, anchor=MSO_ANCHOR.MIDDLE)
    put(box.text_frame, [title], size=21, bold=True, color=BLACK, first=True, space_after=0)
    if subtitle:
        sub = textbox(slide, 0.46, SUB_TOP, 12.40, SUB_H, anchor=MSO_ANCHOR.MIDDLE)
        put(
            sub.text_frame,
            [subtitle],
            size=12,
            bold=True,
            color=RED_DARK,
            first=True,
            space_after=0,
        )
    rect(slide, 0.25, RULE_TOP, 12.83, 0.02, PINK_LINE)
    if page is not None:
        f = textbox(slide, 0.28, 7.02, 9.0, 0.26, anchor=MSO_ANCHOR.MIDDLE)
        put(f.text_frame, [FOOTER_TEXT], size=8.5, color=FOOTER_GREY, first=True, space_after=0)
        n = textbox(slide, 12.30, 7.02, 0.78, 0.26, anchor=MSO_ANCHOR.MIDDLE)
        put(
            n.text_frame,
            [str(page)],
            size=8.5,
            color=FOOTER_GREY,
            align=PP_ALIGN.RIGHT,
            first=True,
            space_after=0,
        )
    return slide


def subhead(slide, text, top, size=12.5, color=RED_DARK, left=0.28, width=12.75):
    """Small section heading inside a content page, with airy spacing."""
    box = textbox(slide, left, top, width, 0.30, anchor=MSO_ANCHOR.MIDDLE)
    put(box.text_frame, [text], size=size, bold=True, color=color, first=True, space_after=0)
    return box


def note(slide, text, top=6.60, size=8.0, left=0.28, width=12.75, height=0.46, color=GREY):
    box = textbox(slide, left, top, width, height)
    put(box.text_frame, [text], size=size, color=color, first=True, space_after=0)


def banner(
    slide, text, top, height=0.62, size=12.5, fill=RED_DARK, color=WHITE, left=0.28, width=12.75
):
    rect(slide, left, top, width, height, fill)
    tb = textbox(slide, left + 0.20, top, width - 0.40, height, anchor=MSO_ANCHOR.MIDDLE)
    put(tb.text_frame, [text], size=size, bold=True, color=color, first=True, space_after=0)


def panel(
    slide,
    l,
    t,
    w,
    h,
    title,
    lines,
    size=11.0,
    fill=PINK_PANEL,
    bar=RED,
    title_size=12.0,
    title_color=RED_DARK,
):
    """Tinted call-out block with a left accent bar."""
    rect(slide, l, t, w, h, fill, line=PINK_LINE)
    rect(slide, l, t, 0.075, h, bar)
    tb = textbox(slide, l + 0.22, t + 0.10, w - 0.44, 0.30, anchor=MSO_ANCHOR.MIDDLE)
    put(
        tb.text_frame,
        [title],
        size=title_size,
        bold=True,
        color=title_color,
        first=True,
        space_after=0,
    )
    bb = textbox(slide, l + 0.22, t + 0.50, w - 0.44, h - 0.62)
    items = []
    for x in lines:
        if isinstance(x, (tuple, list)):
            items.append(x)
        else:
            items.append((x, {"size": size}))
    put(bb.text_frame, items, size=size, space_after=6, first=True)


def divider_page(prs, layout, num, title, bullets, page=None):
    slide = prs.slides.add_slide(layout)
    rect(slide, 0.00, 0.00, 0.14, 7.50, RED)
    rect(slide, 8.60, 0.00, 4.73, 7.50, PINK_PANEL)
    rect(slide, 8.60, 0.00, 0.04, 7.50, PINK_LINE)

    n = textbox(slide, 0.85, 1.30, 5.00, 2.00, anchor=MSO_ANCHOR.MIDDLE)
    put(n.text_frame, [num], size=104, bold=True, color=RED, first=True, space_after=0)
    t = textbox(slide, 0.90, 3.42, 7.30, 0.78, anchor=MSO_ANCHOR.MIDDLE)
    put(t.text_frame, [title], size=34, bold=True, color=BLACK, first=True, space_after=0)
    rect(slide, 0.95, 4.90, 3.20, 0.05, RED)

    b = textbox(slide, 8.95, 1.42, 4.05, 3.20)
    put(
        b.text_frame,
        [("本章核心", {"size": 13, "bold": True, "color": RED})]
        + [(x, {"size": 12.5, "color": GREY, "bullet": True}) for x in bullets],
        size=12.5,
        space_after=12,
        first=True,
    )
    if page is not None:
        f = textbox(slide, 0.85, 6.72, 7.0, 0.26, anchor=MSO_ANCHOR.MIDDLE)
        put(f.text_frame, [FOOTER_TEXT], size=9, color=FOOTER_GREY, first=True, space_after=0)
        nb = textbox(slide, 11.90, 6.72, 1.18, 0.26, anchor=MSO_ANCHOR.MIDDLE)
        put(
            nb.text_frame,
            [str(page)],
            size=9,
            color=FOOTER_GREY,
            align=PP_ALIGN.RIGHT,
            first=True,
            space_after=0,
        )
    return slide


def card(
    slide,
    l,
    t,
    w,
    h,
    title,
    lines,
    title_color=WHITE,
    bar=RED_DARK,
    body_size=10.5,
    title_size=12.5,
    fill=WHITE,
):
    rect(slide, l, t, w, h, fill, line=PINK_LINE)
    rect(slide, l, t, w, 0.34, bar)
    tb = textbox(slide, l + 0.12, t + 0.02, w - 0.24, 0.30, anchor=MSO_ANCHOR.MIDDLE)
    put(
        tb.text_frame,
        [title],
        size=title_size,
        bold=True,
        color=title_color,
        first=True,
        space_after=0,
    )
    bb = textbox(slide, l + 0.14, t + 0.44, w - 0.28, h - 0.58)
    put(
        bb.text_frame,
        [(x, {"size": body_size, "color": BLACK, "bullet": True}) for x in lines],
        size=body_size,
        space_after=7,
        first=True,
    )


# ----------------------------------------------------------------------------
# deck
# ----------------------------------------------------------------------------
def build() -> int:
    OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REF_PPTX, OUT_PPTX)

    prs = Presentation(str(OUT_PPTX))

    # --- wipe every existing slide (keep masters / theme / layouts) ---------
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get(qn("r:id"))
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)

    blank = None
    for lay in prs.slide_masters[0].slide_layouts:
        if lay.name == "Blank":
            blank = lay
            break
    if blank is None:
        blank = prs.slide_masters[0].slide_layouts[6]

    # ================================================================ 1 封面
    s = prs.slides.add_slide(blank)
    rect(s, 0.00, 0.00, 13.33, 0.28, RED_DARK)
    rect(s, 0.00, 7.22, 13.33, 0.28, RED_DARK)
    rect(s, 0.95, 2.62, 11.43, 0.05, RED)

    b = textbox(s, 0.95, 1.56, 11.43, 0.62, anchor=MSO_ANCHOR.MIDDLE)
    put(
        b.text_frame,
        ["重组乙型肝炎疫苗（汉逊酵母，CpG 和铝佐剂）"],
        size=25,
        bold=True,
        color=BLACK,
        align=PP_ALIGN.CENTER,
        first=True,
        space_after=0,
    )
    b = textbox(s, 0.95, 2.86, 11.43, 0.76, anchor=MSO_ANCHOR.MIDDLE)
    put(
        b.text_frame,
        ["Ⅰ期细胞免疫评价 与同类 CpG 佐剂乙肝疫苗对比分析"],
        size=27,
        bold=True,
        color=RED,
        align=PP_ALIGN.CENTER,
        first=True,
        space_after=0,
    )
    b = textbox(s, 0.95, 3.76, 11.43, 0.40, anchor=MSO_ANCHOR.MIDDLE)
    put(
        b.text_frame,
        ["检测指标差异  ·  检测结果差异  ·  可比性判定  ·  综合评估与建议"],
        size=15,
        bold=False,
        color=GREY,
        align=PP_ALIGN.CENTER,
        first=True,
        space_after=0,
    )

    rect(s, 5.42, 4.36, 2.50, 0.035, PINK_LINE)
    b = textbox(s, 0.95, 4.66, 11.43, 0.34, anchor=MSO_ANCHOR.MIDDLE)
    put(
        b.text_frame,
        ["YDSWX（TVAX-009）-001（Ⅰ）  |  数据截止：Ⅰ期临床研究总结报告 V1.0（2025-06-18）"],
        size=11,
        color=GREY,
        align=PP_ALIGN.CENTER,
        first=True,
        space_after=0,
    )

    b = textbox(s, 2.16, 5.72, 9.00, 1.10, anchor=MSO_ANCHOR.TOP)
    put(
        b.text_frame,
        [
            (
                "远大赛威信生命科学（南京）有限公司",
                {"size": 16, "bold": True, "align": PP_ALIGN.CENTER},
            ),
            ("2026 年 09 月", {"size": 16, "bold": True, "align": PP_ALIGN.CENTER, "color": RED}),
        ],
        space_after=10,
        first=True,
    )

    # ================================================================ 2 目录
    s = content_page(prs, blank, "汇报内容", page=2)
    items = [
        (
            "01",
            "细胞免疫检测指标差异",
            [
                "本品 / 原研 HEPLISAV-B / 同类 CpG 参照的研究设计对照",
                "原研 CMI 证据的三个层级与其实测数据",
                "CpG 佐剂乙肝疫苗 CMI 检测实践一览",
            ],
        ),
        (
            "02",
            "细胞免疫检测结果差异",
            [
                "Ⅰ期 IL-2 / IFN-γ / IP-10 实测数据",
                "与同类 CpG 乙肝疫苗 CMI 结果横向比较",
                "四项关键判读结论",
            ],
        ),
        ("03", "可比性判定", ["六要素可比性矩阵", "跨品种比较能回答与不能回答的问题"]),
        ("04", "综合评估与后续建议", ["方法学与数据质量评价", "注册申报口径建议与后续研究建议"]),
    ]
    top = 1.20
    for i, (num, title, lines) in enumerate(items):
        col = i % 2
        row = i // 2
        l = 0.35 + col * 6.45
        t = top + row * 2.60
        rect(s, l, t, 6.15, 2.28, WHITE, line=PINK_LINE)
        rect(s, l, t, 0.075, 2.28, RED)
        nb = textbox(s, l + 0.25, t + 0.20, 1.30, 0.72, anchor=MSO_ANCHOR.MIDDLE)
        put(nb.text_frame, [num], size=34, bold=True, color=RED, first=True, space_after=0)
        tb = textbox(s, l + 1.35, t + 0.24, 4.60, 0.58, anchor=MSO_ANCHOR.MIDDLE)
        put(tb.text_frame, [title], size=16, bold=True, color=BLACK, first=True, space_after=0)
        rect(s, l + 1.38, t + 0.92, 4.40, 0.02, PINK_LINE)
        lb = textbox(s, l + 1.38, t + 1.06, 4.55, 1.10)
        put(
            lb.text_frame,
            [(x, {"size": 11, "color": GREY, "bullet": True}) for x in lines],
            size=11,
            space_after=8,
            first=True,
        )

    # ================================================================ 3 分隔 01
    divider_page(
        prs,
        blank,
        "01",
        "细胞免疫检测指标差异",
        [
            "三品种研究设计对照：本品 / 原研 / 同类 CpG 参照",
            "原研注册临床未设 CMI 终点（三个证据层级核查）",
            "但原研存在非临床与研究性人体 CMI 实测数据",
            "CpG 佐剂乙肝疫苗 CMI 检测实践横向一览",
        ],
        page=3,
    )

    # ================================================================ 4 设计对照
    s = content_page(
        prs,
        blank,
        "对比基础：三品种研究设计对照",
        "同为“HBsAg + CpG 类 TLR9 激动剂”技术路线，但佐剂分子、是否含铝、免疫程序与受试人群均不同",
        page=4,
    )
    rows = [
        [
            "对比项",
            "TVAX-009 Ⅰ期（本品）",
            "HEPLISAV-B Ⅰ期（原研）",
            "CPG 7909 + Engerix-B（同类 CpG 参照）",
        ],
        [
            "研究 / 文献",
            "YDSWX（TVAX-009）-001（Ⅰ）",
            "Halperin 等，Vaccine 21 (2003) 2461–2467",
            "Halperin 等，Vaccine 2003；Cooper 等，J Clin Immunol 2004；Angel & Cooper，JIBTV 2008",
        ],
        [
            "抗原与佐剂系统",
            "重组 HBsAg 20 μg（汉逊酵母）\n氢氧化铝 + CpG-QCX1（200 / 500 / 1000 μg）",
            "重组 HBsAg 20 μg（酵母）\n无铝佐剂，1018 ISS（300 / 650 / 1000 / 3000 μg）",
            "Engerix-B 40 μg HBsAg（铝佐剂）\n± CPG 7909（B 类 CpG ODN，0.125 / 0.5 / 1.0 mg）",
        ],
        [
            "免疫程序",
            "0、1、6 月，三剂，肌内注射",
            "0、2 月，两剂，肌内注射",
            "0、1、2 月 或 0、4、8 周，三剂，肌内注射",
        ],
        [
            "受试人群",
            "18 岁及以上 120 例（18–59 岁 96 例；≥60 岁 24 例）",
            "18–55 岁健康成人 48 例",
            "健康成人 18–35 岁；HIV 感染已抑制者 18–55 岁 38 例",
        ],
        ["主要终点", "安全性与耐受性", "安全性与耐受性", "安全性与耐受性"],
        [
            "体液免疫指标",
            "抗-HBs 阳转率、GMC（化学发光法）",
            "抗-HBs 阳转率、GMT（AUSAB EIA）",
            "抗-HBs 血清保护率、GMT",
        ],
        [
            "细胞免疫指标",
            "有（探索性）：ICS 检测 IL-2、IFN-γ；MSD 检测 IP-10",
            "未设置",
            "有：⁵¹Cr 释放 CTL 试验；LPR（³H-TdR 掺入）",
        ],
        [
            "CMI 样本量",
            "60 例（前三个入组步骤各前 20 例 18–59 岁）",
            "—",
            "健康成人各亚组 7–9 例；HIV 人群每组 19 例",
        ],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[1.72, 3.55, 3.60, 3.88],
        row_h=0.46,
        header_h=0.42,
        fsize=9.4,
        hsize=10.5,
        red_cells={(7, 1), (7, 2), (7, 3)},
        aligns={0: PP_ALIGN.LEFT, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.LEFT, 3: PP_ALIGN.LEFT},
    )
    note(
        s,
        "注：本表基于Ⅰ期临床研究总结报告 V1.0（2025-06-18）与项目文献库内 HEPLISAV-B、CPG 7909 + Engerix-B 文献整理。"
        "三者人群、免疫程序与佐剂构成均不同，任何跨研究比较均须以该差异为前提。",
        top=5.50,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 5 差异①
    s = content_page(
        prs,
        blank,
        "差异①：注册临床开发中细胞免疫检测的“有 / 无”",
        "须区分“注册临床未设 CMI 终点”与“原研从未做过细胞免疫研究”——后者并不成立",
        page=5,
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        4.85,
        "TVAX-009 Ⅰ期：已设置细胞免疫探索终点",
        [
            "检测项目：抗原特异性细胞因子 IL-2、IFN-γ（ICS 胞内细胞因子染色）；IP-10（MSD 电化学发光法）",
            "检测单位：昭衍（苏州）新药研究中心有限公司",
            "采样时点：首剂接种前、第 2 剂接种后 1 个月、第 3 剂接种后 1 个月",
            "样本量：60 例 18–59 岁受试者（各组 15 例）",
            "采血量：ICS 8.0–9.0 mL；IP-10 3.0–4.0 mL",
            "分析集：FAS、PPS2、PPS4；中位数（Q1, Q3）描述，秩和检验",
        ],
        bar=RED_DARK,
        body_size=10.5,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        4.85,
        "HEPLISAV-B：注册临床开发中未设 CMI 终点",
        [
            "2003 年Ⅰ期（Halperin 等）：仅检测抗-HBs（AUSAB EIA）与安全性实验室指标，无 T 细胞检测",
            "关键Ⅲ期（DV2-HBV-10 / -16 / -23）：主要免疫原性终点为血清保护率（SPR），无 CMI 终点",
            "FDA/CBER 2017 临床审评报告：免疫原性章节仅评述体液免疫（SPR 95.4%，95%CI 94.8–96.0）",
            "FDA 说明书（2024-09）与 EMA 审评报告：临床药效学研究“评估的是抗-HBs 抗体应答”，无 CMI 数据",
            "本项目文献库 23 份 HEPLISAV-B 文件中，未见任何 ELISPOT / ICS / 胞内细胞因子染色的临床检测数据",
        ],
        bar=GREY,
        body_size=10.5,
    )
    note(
        s,
        "重要限定：上述结论仅针对“原研注册临床开发资料”，不能解读为“原研从未开展细胞免疫研究”。"
        "原研另有非临床（动物）与研究者在慢性乙肝治疗性场景发起的人体细胞免疫研究，详见第 7–8 页。",
        top=6.15,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 6 差异②
    s = content_page(
        prs,
        blank,
        "差异②：细胞免疫检测指标体系逐项对比",
        "在“健康人群预防性接种”这一共同场景下，两套体系在“是否检测、检测什么、如何读值”层面均无交集",
        page=6,
    )
    rows = [
        ["对比维度", "TVAX-009 Ⅰ期", "HEPLISAV-B（原研）"],
        ["注册临床是否设置 CMI 终点", "是（探索性终点）", "否（未见 CMI 终点）"],
        ["注册临床检测平台", "ICS 流式胞内细胞因子染色 + MSD 电化学发光", "无临床 CMI 平台"],
        ["靶细胞 / 门控策略", "CD45⁺CD3⁺（T 细胞门控）", "—"],
        ["细胞因子谱", "IL-2、IFN-γ（胞内）；IP-10（上清 / 血清）", "—"],
        ["读值与单位", "阳性细胞百分比（%）；pg/mL", "—"],
        ["采样时点", "免前、第 2 剂后 1 月、第 3 剂后 1 月", "—"],
        ["样本类型与用量", "染色全血 8.0–9.0 mL；血清 3.0–4.0 mL", "—"],
        ["抗原刺激条件", "CSR 未披露刺激物（全长 HBsAg / 肽池）、浓度与时长", "—"],
        ["阳性判定阈值", "CSR 未披露具体阈值与阴 / 阳性对照设置", "—"],
        ["体液免疫指标", "抗-HBs 阳转率、GMC（化学发光法）", "抗-HBs SPR、GMT（EIA / 化学发光）"],
        [
            "非临床 / 研究性 CMI 研究",
            "未纳入本次对比",
            "有（动物 Th1 偏向；人体 LPR 与微阵列；慢性乙肝治疗性研究，见下两页）",
        ],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[3.10, 5.10, 4.55],
        row_h=0.385,
        header_h=0.40,
        fsize=9.8,
        hsize=10.5,
        red_cells={(1, 1), (1, 2), (8, 1), (9, 1), (11, 2)},
        aligns={0: PP_ALIGN.LEFT, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.LEFT},
    )
    note(
        s,
        "结论：在“健康人群预防性接种”这一共同场景下，原研一侧不存在可对照的临床细胞免疫数据集，"
        "两者在检测指标层面无法建立一一对应关系，亦不具备进行数值头对头比较的方法学基础。",
        top=5.92,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 7 证据全景
    s = content_page(
        prs,
        blank,
        "原研细胞免疫研究证据全景：三个层级",
        "“注册临床未设 CMI 终点”≠“原研未开展细胞免疫研究”——须分层看待",
        page=7,
    )
    rows = [
        ["证据层级", "研究 / 来源", "是否含细胞免疫检测", "与本品的对照价值"],
        [
            "注册临床\n（预防适应症）",
            "HEPLISAV-B Ⅰ期（2003）；Ⅱ/Ⅲ期（DV2-HBV-10 / -16 / -23）；\nFDA 与 EMA 说明书、CBER 与 EMA 审评报告",
            "否\n仅体液免疫（SPR / GMT）",
            "无 CMI 数据可比对",
        ],
        [
            "非临床\n（动物与人体细胞）",
            "CpG 1018 + HBsAg：小鼠、大鼠、狒狒（Dynavax / EMA EPAR）；\n体外人 PBMC 与纯化 B 细胞；HBV-22 人体微阵列研究",
            "有\nIgG2a / IgG1 亚型（Th1 偏倚）；人 PBMC 的 IL-12、IL-6、IFN-α；\nIFN 调控基因激活",
            "机制佐证，\n部分为人体材料",
        ],
        [
            "研究者发起临床\n（治疗性 / 免疫抑制场景）",
            "CPG 7909 + Engerix-B：HIV 感染者 LPR 研究（Angel & Cooper，2008）；\nBOOST-9（NCT04843852，慢性乙肝）；TherVacB（NCT05727267，含 HEPLISAV-B 组）",
            "有\nLPR（³H-TdR 掺入）、淋巴细胞亚群表型；\nBOOST-9 / TherVacB 登记含免疫学终点（结果未发表）",
            "方法学可参照；\n人群与场景不同",
        ],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[1.95, 4.45, 3.60, 2.75],
        row_h=1.06,
        header_h=0.40,
        fsize=9.2,
        hsize=10.0,
        red_cells={(1, 2), (2, 2), (3, 2)},
        aligns={0: PP_ALIGN.CENTER, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.LEFT, 3: PP_ALIGN.LEFT},
    )
    panel(
        s,
        0.28,
        4.72,
        12.75,
        1.70,
        "对方法学的直接借鉴：BOOST-9 登记的免疫学检测组合（建议作为我们 assay 升级的参照系）",
        [
            (
                "① 多细胞因子产率：IFN-γ、TNF-α、IL-2、IL-12、IL-21　　　"
                "② 免疫表型：CD38、HLA-DR、PD-1、CD28　　　"
                "③ 滤泡辅助 T 细胞（Tfh）功能试验",
                {"size": 11, "bold": True},
            ),
            (
                "④ HBsAg 特异性免疫细胞类型（百分比）与功能（产细胞因子细胞百分比）；"
                "采样时点：基线、第 2、4、8、24 周",
                {"size": 11},
            ),
            (
                "提示：该组合较我们现有的“IL-2 / IFN-γ / IP-10”三项显著更宽，尤其 Tfh 功能试验与 PD-1 表型"
                "更贴近 CpG 佐剂的作用通路。",
                {"size": 11, "bold": True, "color": RED_DARK},
            ),
        ],
        size=11,
    )
    note(
        s,
        "来源：ClinicalTrials.gov NCT04843852（BOOST-9，Univ. of Maryland，2025-10 启动，主要完成时间预计 2026-10，结果尚未发表）；"
        "NCT05727267（TherVacB，已完成，结果未公布）；Angel & Cooper，J Immune Based Ther Vaccines 2008;6:4。",
        top=6.55,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 8 原研 CMI 实测
    s = content_page(
        prs,
        blank,
        "原研细胞免疫实测数据：非临床与人体研究",
        "“注册临床无 CMI”不等于“原研无细胞免疫数据”——以下为文献库已核实的具体结果",
        page=8,
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        2.30,
        "非临床：动物免疫原性（EMA EPAR）",
        [
            "小鼠抗体亚型：HBsAg + 1018 ISS 以 IgG2a 为主，HBsAg 单用与 Engerix-B 以 IgG1 为主 → 1018 ISS 使应答向 Th1 型偏倚",
            "狒狒剂量-效应：3000 μg 的 1018 ISS 方达 100% 血清保护率；抗原 / 佐剂最优比为 1 / 150",
            "狒狒体内（非 GLP）：0、1、6 h 未见 IL-12、IL-6、IL-8、IFN-γ、TNF-α 的显著诱导",
        ],
        bar=RED_DARK,
        body_size=9.8,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        2.30,
        "非临床 / 人体细胞：TLR9 通路激活（EMA EPAR）",
        [
            "体外人 PBMC 与纯化 B 细胞：诱导 IL-12、IL-6、IFN-α，并具丝裂原活性，证实 1018 ISS 可激活人免疫细胞",
            "HBV-22 人体微阵列研究：IFN 调控基因快速、显著激活，反映 pDC 来源 I 型 IFN 的诱导",
            "但审评原文同时指出：B 细胞、T 细胞与 DC 未见显著表型改变，该数据需谨慎解读",
        ],
        bar=RED_DARK,
        body_size=9.8,
    )
    card(
        s,
        0.28,
        3.52,
        6.20,
        2.30,
        "人体抗原特异性 CMI：CPG 7909 + Engerix-B（HIV 感染人群）",
        [
            "LPR（³H-TdR 掺入）：CpG 组各时点增殖应答均更高，8 周 p = 0.042、48 周 p = 0.024",
            "48 周 SI ≥ 5 阳性率：8 / 19（42%）vs 3 / 19（16%），p = 0.07（未达统计学显著）",
            "对 HIV p24 及回忆抗原无增强；CD4 / CD8 及记忆、活化亚群均无变化",
        ],
        bar=RED_DARK,
        body_size=9.8,
    )
    card(
        s,
        6.82,
        3.52,
        6.22,
        2.30,
        "治疗性场景动物模型：AAV-HBV 慢性乙肝小鼠",
        [
            "HEPLISAV-B 2 剂：血清 HBV DNA 降约 1000 倍、HBsAg 转阴，ALT 不变 → 非细胞溶解机制",
            "HBs 特异性 IFN-γ ELISPOT 升高；CD4⁺ 与 CD8⁺ T 细胞的 IFN-γ、TNF-α 产率提高",
            "CD4 清除使疗效完全消失，CD8 清除不影响；抗 CD40L 阻断使疗效完全消失",
        ],
        bar=GREY,
        body_size=9.8,
    )
    note(
        s,
        "来源：EMA/1767/2021 HEPLISAV-B 公开审评报告（EMA EPAR）；Angel & Cooper，J Immune Based Ther Vaccines 2008;6:4（PMID 18700037）；"
        "Ahodantin 等，bioRxiv 2026（AAV-HBV 小鼠模型，预印本，未经同行评议）。"
        "注：CPG 7909 与 1018 ISS 同属 B 类 CpG ODN 但序列不同，其人体 CMI 数据不可直接等同于 HEPLISAV-B。",
        top=6.05,
        left=0.28,
        width=12.75,
        height=0.62,
    )

    # ================================================================ 9 检测实践一览
    s = content_page(
        prs,
        blank,
        "CpG 佐剂乙肝疫苗细胞免疫检测实践一览",
        "横向比较可见：CMI 检测并非本品独有，但各品种的平台、指标与成熟度差异显著",
        page=9,
    )
    rows = [
        ["产品 / 组合", "研究阶段与人群", "CMI 检测方法与指标", "关键限定"],
        [
            "TVAX-009\n（CpG-QCX1 + 铝佐剂）",
            "Ⅰ期，健康成人 18–59 岁，60 例",
            "ICS 流式胞内细胞因子染色 + MSD 电化学发光\nIL-2、IFN-γ（CD45⁺CD3⁺ 门控，%）；IP-10（pg/mL）",
            "探索性终点；CSR 未披露刺激物、浓度、时长与阳性判定阈值",
        ],
        [
            "HEPLISAV-B\n（CpG 1018，无铝）",
            "注册临床 Ⅰ–Ⅲ期，健康成人 18–70 岁",
            "未设 CMI 检测\n免疫原性终点为 SPR / GMT",
            "注册开发中无人体 CMI 数据集",
        ],
        [
            "CPG 7909 + Engerix-B\n（健康成人）",
            "Ⅰ / Ⅱ期，健康成人 18–35 岁",
            "⁵¹Cr 释放 CTL 试验\nPBMC 经 5 天再刺激后检测 HBsAg 特异性 CTL",
            "因技术困难数据不完整；阳性率呈剂量趋势但 p > 0.05",
        ],
        [
            "CPG 7909 + Engerix-B\n（HIV 感染已抑制者）",
            "Ⅰb / Ⅱa 期，HIV 感染者 18–55 岁，38 例",
            "LPR（³H-TdR 掺入）+ 淋巴细胞亚群免疫表型\nHBsAg 特异性刺激指数（SI）",
            "6 天培养；SI ≥ 5 判阳；亚群表型未见变化",
        ],
        [
            "TherVacB\n（含 HEPLISAV-B 初免组）",
            "Ⅰa 期，健康成人 18–65 岁，26 例（已完成）",
            "次要终点含“HBV 特异性 T 细胞应答强度”\n具体方法与读值未公开",
            "结果尚未公布；样本量小",
        ],
        [
            "BOOST-9\n（HEPLISAV-B，慢性乙肝）",
            "Ⅰ期，慢性乙肝已抑制者，10 例（入组中）",
            "其他终点含“免疫学与病毒学应答变化”\n具体方法未公开",
            "结果未发表；治疗性场景，非预防性",
        ],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[2.45, 2.70, 3.75, 3.85],
        row_h=0.70,
        header_h=0.42,
        fsize=9.0,
        hsize=10.0,
        red_cells={(1, 2)},
        aligns={0: PP_ALIGN.LEFT, 1: PP_ALIGN.LEFT, 2: PP_ALIGN.LEFT, 3: PP_ALIGN.LEFT},
    )
    note(
        s,
        "来源：Ⅰ期临床研究总结报告 V1.0（2025-06-18）；EMA/1767/2021；本项目文献库 CPG 7909 + Engerix-B 系列文献；"
        "ClinicalTrials.gov NCT04843852、NCT05727267（登记记录，非同行评议文献）。",
        top=5.95,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 10 差异③
    s = content_page(
        prs,
        blank,
        "差异③：机制（MoA）表述与证据层级",
        "原研“有细胞免疫研究” ≠ “有可供桥接的健康人群预防性 CMI 数据集”",
        page=10,
    )
    panel(
        s,
        0.28,
        BODY_TOP,
        12.75,
        1.62,
        "HEPLISAV-B 作用机制通路（FDA 说明书 / EMA SmPC / EMA 与 CBER 审评报告原文归纳）",
        [
            (
                "CpG 1018  →  TLR9（浆细胞样树突状细胞 pDC、B 细胞）  →  分泌 IFN-α、IL-12  →  "
                "促进 Th1 型 CD4⁺ T 细胞分化  →  辅助 B 细胞",
                {"size": 12, "bold": True},
            ),
            (
                "→  大量抗-HBs 分泌型浆细胞 + HBsAg 特异性记忆 B / T 细胞  →  高而持久的抗体应答",
                {"size": 12, "bold": True, "color": RED_DARK},
            ),
        ],
        size=12,
    )
    card(
        s,
        0.28,
        2.92,
        6.20,
        2.55,
        "要点一：MoA 属机制阐述，非实测数据",
        [
            "说明书中的 Th1 偏向、CD4⁺ T 细胞分化等表述，来源于体外 / 非临床研究与机制推断",
            "在公开的注册临床研究与注册资料中，未见配套的人体抗原特异性 T 细胞检测数据支撑",
            "FDA 审评原文明确指出：“1018 佐剂的完整作用机制尚不明确”",
        ],
        bar=RED_DARK,
        body_size=10.5,
    )
    card(
        s,
        6.82,
        2.92,
        6.22,
        2.55,
        "要点二：现有 T 细胞证据的场景差异",
        [
            "非临床：小鼠研究显示 HBsAg 特异性 T / B 细胞免疫增强，疗效依赖 CD4⁺ T 细胞与 CD40 / CD40L，与 CD8 无关",
            "人体：CPG 7909 的 LPR 研究在 HIV 感染人群、BOOST-9 面向慢性乙肝“治疗性”接种，均非健康人群“预防性”接种",
            "结论：证据存在，但因人群、目的（治疗 vs 预防）与程序不同，不能作为本品的桥接参照",
        ],
        bar=RED_DARK,
        body_size=10.5,
    )
    note(
        s,
        "来源：FDA HEPLISAV-B 说明书（2024-09）5.1 药效学性质；EMA SmPC 5.1；EMA/1767/2021；FDA/CBER Clinical Review（2017-11-09）§4.4.1。",
        top=5.72,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 11 分隔 02
    divider_page(
        prs,
        blank,
        "02",
        "细胞免疫检测结果差异",
        [
            "TVAX-009 Ⅰ期 IL-2 / IFN-γ / IP-10 实测数据",
            "与同类 CpG 乙肝疫苗 CMI 结果横向比较",
            "四项关键判读结论",
            "阴性结果的归因：assay 分辨力 vs 疫苗效应",
        ],
        page=11,
    )

    # ================================================================ 12 实测结果
    s = content_page(
        prs,
        blank,
        "TVAX-009 Ⅰ期细胞免疫实测结果（18–59 岁，中位数）",
        "胞内细胞因子染色（ICS）检测 IL-2、IFN-γ；电化学发光法（MSD）检测 IP-10",
        page=12,
    )
    subhead(s, "① 第 2 剂接种后 1 个月（PPS2）", top=0.98)
    rows = [
        [
            "细胞因子",
            "检测时点",
            "低剂量组\n(N=15)",
            "中剂量组\n(N=15)",
            "高剂量组\n(N=14)",
            "对照组\n(N=15)",
            "P 值",
        ],
        ["IL-2 (%)", "首剂接种前", "0.100", "0.100", "0.100", "0.100", "0.6938"],
        ["", "第 2 剂后 1 个月", "0.000", "0.100", "0.100", "0.100", "0.1525"],
        ["IFN-γ (%)", "首剂接种前", "0.100", "0.000", "0.000", "0.100", "<0.0001"],
        ["", "第 2 剂后 1 个月", "0.100", "0.100", "0.000", "0.100", "0.7322"],
        ["IP-10 (pg/mL)", "首剂接种前", "193.0", "175.0", "175.5", "178.0", "0.9459"],
        ["", "第 2 剂后 1 个月", "318.0", "294.0", "195.5", "263.0", "0.0797"],
    ]
    make_table(
        s,
        0.28,
        1.30,
        12.75,
        rows,
        col_widths=[2.05, 2.55, 1.62, 1.62, 1.62, 1.62, 1.67],
        row_h=0.32,
        header_h=0.44,
        fsize=10.0,
        hsize=10.0,
    )

    subhead(s, "② 第 3 剂接种后 1 个月（PPS4）", top=3.74)
    rows = [
        [
            "细胞因子",
            "检测时点",
            "低剂量组\n(N=15)",
            "中剂量组\n(N=14)",
            "高剂量组\n(N=14)",
            "对照组\n(N=15)",
            "P 值",
        ],
        ["IL-2 (%)", "首剂接种前", "0.100", "0.100", "0.100", "0.100", "0.7472"],
        ["", "第 3 剂后 1 个月", "0.000", "0.100", "0.100", "0.100", "0.0018"],
        ["IFN-γ (%)", "首剂接种前", "0.100", "0.000", "0.000", "0.100", "0.0001"],
        ["", "第 3 剂后 1 个月", "0.100", "0.100", "0.100", "0.100", "0.4010"],
        ["IP-10 (pg/mL)", "首剂接种前", "193.0", "174.5", "175.5", "178.0", "0.9484"],
        ["", "第 3 剂后 1 个月", "266.0", "252.5", "204.0", "281.0", "0.5164"],
    ]
    make_table(
        s,
        0.28,
        4.06,
        12.75,
        rows,
        col_widths=[2.05, 2.55, 1.62, 1.62, 1.62, 1.62, 1.67],
        row_h=0.32,
        header_h=0.44,
        fsize=10.0,
        hsize=10.0,
    )
    note(
        s,
        "注：读值为 CD45⁺CD3⁺IL-2⁺、CD45⁺CD3⁺IFN-γ⁺ 细胞百分比中位数与 IP-10 浓度中位数；对照组为不含 CpG-QCX1 的重组乙型肝炎疫苗"
        "（汉逊酵母，艾美诚信）。数据来源于Ⅰ期临床研究总结报告 V1.0（2025-06-18）表 12–31、12–32。",
        top=6.52,
        left=0.28,
        width=12.75,
        height=0.42,
        size=7.8,
    )

    # ================================================================ 13 结果横向比较
    s = content_page(
        prs,
        blank,
        "同类 CpG 乙肝疫苗细胞免疫结果横向比较",
        "在健康人群预防性接种场景下，“检出方向性信号但难以达到统计学显著”是同类产品的共同特征",
        page=13,
    )
    rows = [
        ["研究 / 产品", "人群", "CMI 指标", "主要结果", "与本品的可比性"],
        [
            "TVAX-009 Ⅰ期（本品）",
            "健康成人 18–59 岁，60 例",
            "IL-2、IFN-γ（ICS，%）；IP-10（MSD，pg/mL）",
            "IL-2 / IFN-γ 免疫后较免前无明显变化；IP-10 升高但无剂量-效应关系；与不含 CpG 的对照无区分",
            "基准",
        ],
        [
            "CPG 7909 + Engerix-B（健康成人）",
            "健康成人 18–35 岁",
            "⁵¹Cr 释放 CTL 试验（HBsAg 特异性）",
            "CTL 阳性率随剂量由 14%（1 / 7）升至 44%（4 / 9）；但 p > 0.05，且因技术困难数据不完整",
            "趋势可比：\n同样未达显著",
        ],
        [
            "CPG 7909 + Engerix-B（HIV 感染已抑制者）",
            "HIV 感染、HAART 已抑制，38 例",
            "LPR（³H-TdR 掺入），刺激指数 SI",
            "8 周 p = 0.042、48 周 p = 0.024；48 周 SI ≥ 5 阳性率 42% vs 16%（p = 0.07）",
            "方向一致；\n平台与人群不同",
        ],
        [
            "HEPLISAV-B（注册临床）",
            "健康成人 18–70 岁，逾 1.4 万例",
            "未设 CMI 终点",
            "仅体液免疫：SPR 90.0%–95.0%，显著优于 Engerix-B",
            "无可比对数据",
        ],
        [
            "HEPLISAV-B（AAV-HBV 小鼠）",
            "慢性乙肝小鼠模型",
            "IFN-γ ELISPOT；胞内细胞因子流式",
            "HBs 特异性 IFN-γ ELISPOT 升高；CD4⁺ / CD8⁺ T 细胞 IFN-γ、TNF-α 产率提高；疗效依赖 CD4 与 CD40 / CD40L",
            "动物数据，\n仅机制参照",
        ],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[2.30, 1.95, 2.55, 4.15, 1.80],
        row_h=0.78,
        header_h=0.42,
        fsize=9.0,
        hsize=10.0,
        aligns={
            0: PP_ALIGN.LEFT,
            1: PP_ALIGN.LEFT,
            2: PP_ALIGN.LEFT,
            3: PP_ALIGN.LEFT,
            4: PP_ALIGN.LEFT,
        },
    )
    banner(
        s,
        "关键发现：在健康人群预防性接种场景下，已公开的 CpG 佐剂乙肝疫苗人体细胞免疫数据普遍呈现"
        "“方向性信号存在、但难以达到统计学显著、且受 assay 性能限制”的共同特征。",
        top=5.46,
        height=0.66,
        size=12.0,
    )
    note(
        s,
        "来源：Ⅰ期临床研究总结报告 V1.0（2025-06-18）；本项目文献库 CPG 7909 + Engerix-B Ⅰ/Ⅱ期文献；"
        "Angel & Cooper，JIBTV 2008;6:4；EMA/1767/2021；Ahodantin 等，bioRxiv 2026（预印本）。",
        top=6.28,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 14 结果判读
    s = content_page(
        prs, blank, "结果判读：四项关键结论", "均为描述性、探索性结论，不作为有效性依据", page=14
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        2.18,
        "① IL-2 / IFN-γ：免疫后较免前变化不明显",
        [
            "各剂量组与对照组 CD45⁺CD3⁺IL-2⁺、CD45⁺CD3⁺IFN-γ⁺ 细胞百分比中位数多落在 0.000%–0.100% 区间",
            "第 2 剂、第 3 剂接种后 1 个月与首剂接种前相比，变化均不明显",
            "多数时点组间差异无统计学意义（仅免前 IFN-γ 基线存在组间差异）",
        ],
        bar=RED_DARK,
        body_size=10.0,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        2.18,
        "② IP-10：普遍升高，但无剂量-效应关系",
        [
            "第 2 剂后 1 个月，各组 IP-10 中位浓度由免前 175–193 pg/mL 升至 195.5–318 pg/mL",
            "低、中、高剂量组之间未见剂量-效应关系（高剂量组反而最低）",
            "不含 CpG 的阳性对照组同样升高（263.0 pg/mL），升幅与试验组相当",
        ],
        bar=RED_DARK,
        body_size=10.0,
    )
    card(
        s,
        0.28,
        3.40,
        6.20,
        2.18,
        "③ 未能与不含 CpG 的对照疫苗区分",
        [
            "Ⅰ期细胞免疫指标未能将 CpG-QCX1 各剂量组与不含 CpG 的铝佐剂对照疫苗区分开",
            "该结果更倾向于提示：现有 assay 的分辨力不足以捕捉 CpG 佐剂的细胞免疫效应",
            "而非证明“疫苗不产生细胞免疫效应”——两者不可混为一谈",
        ],
        bar=RED_DARK,
        body_size=10.0,
    )
    card(
        s,
        6.82,
        3.40,
        6.22,
        2.18,
        "④ “检测不到”是同类产品的共性难点",
        [
            "CPG 7909 + Engerix-B 健康成人 ⁵¹Cr CTL 试验：阳性率随剂量 14% → 44%，但 p > 0.05 且数据不完整",
            "CPG 7909 + Engerix-B 在 HIV 人群的 LPR：组间差异显著（p = 0.042 / 0.024），但阳性率 42% vs 16% 仅 p = 0.07",
            "提示：在本行业现有 assay 灵敏度下，“未检出显著差异”是共性难点，而非本品特有的阴性发现",
        ],
        bar=GREY,
        body_size=10.0,
    )
    note(
        s,
        "注：上述判读与Ⅰ期临床研究总结报告结论一致：“第 2 剂、第 3 剂接种后 1 个月，低、中、高剂量组和对照组细胞因子 IL-2、IFN-γ 水平较首剂接种前均无明显变化；"
        "IP-10 浓度较首剂接种前均有所升高，但三个剂量组间未见明显剂量-效应关系。”",
        top=5.72,
        left=0.28,
        width=12.75,
        height=0.60,
        size=7.8,
    )

    # ================================================================ 15 分隔 03
    divider_page(
        prs,
        blank,
        "03",
        "可比性判定",
        [
            "六要素可比性矩阵逐项核查",
            "能否与原研 / 同类产品进行头对头比较",
            "跨品种比较可以回答的问题",
            "跨品种比较不能回答的问题",
        ],
        page=15,
    )

    # ================================================================ 16 可比性矩阵
    s = content_page(
        prs,
        blank,
        "可比性判定：能否进行头对头比较",
        "逐要素核查后，结论为：不可进行数值层面的头对头比较",
        page=16,
    )
    _ok, no, mid = "✓ 满足", "✗ 不满足", "△ 部分满足"
    rows = [
        ["可比性要素", "判定", "说明"],
        [
            "同一检测平台与试剂",
            no,
            "原研注册临床无 CMI 平台；其人体 CMI 数据来自体外研究与研究者发起研究，无法建立平台对应关系",
        ],
        ["同一读值与计量单位", no, "本品为阳性细胞百分比（%）与 pg/mL；原研无同场景对应读值"],
        ["同一采样时点与免疫程序", no, "本品 0、1、6 月三剂；原研注册研究为 0、1 月两剂"],
        ["同一抗原刺激条件", no, "双方均未公开披露刺激物、浓度、刺激时长与对照设置"],
        ["同一佐剂分子", no, "CpG-QCX1 + 氢氧化铝  vs  1018 ISS（无铝）；CPG 7909 亦为不同序列"],
        [
            "同一免疫场景",
            no,
            "本品为健康人群预防性接种；原研人体 CMI 研究为慢性乙肝治疗性或 HIV 免疫抑制场景",
        ],
        ["同一目标人群", mid, "均为成人，但样本量、基线免疫状态与合并疾病不同"],
        ["同一体液免疫锚点", mid, "均以抗-HBs ≥ 10 mIU/mL 为血清学保护阈值，可用于间接参照"],
    ]
    make_table(
        s,
        0.28,
        BODY_TOP,
        12.75,
        rows,
        col_widths=[3.10, 1.75, 7.90],
        row_h=0.44,
        header_h=0.42,
        fsize=10.0,
        hsize=11,
        red_cells={(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)},
        aligns={0: PP_ALIGN.LEFT, 1: PP_ALIGN.CENTER, 2: PP_ALIGN.LEFT},
    )
    banner(
        s,
        "综合判定：不可进行数值头对头比较。原研与同类 CpG 产品的细胞免疫数据分布于非临床、"
        "体外人细胞与治疗性 / 免疫抑制场景，与本品的健康人群预防性场景不可直接对照；建议仅作定性与方法学层面借鉴。",
        top=5.26,
        height=0.66,
        size=12.0,
    )
    note(
        s,
        "注：“△ 部分满足”指该要素具备一定参照价值，但不足以支撑定量桥接。同类产品的方法学设计"
        "（多细胞因子产率、免疫表型、Tfh 功能试验、ELISPOT / AIM）仍可供我们升级 assay 时借鉴。",
        top=6.08,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 17 比较边界
    s = content_page(
        prs,
        blank,
        "跨品种比较的边界：能回答什么、不能回答什么",
        "明确边界，是避免监管沟通中被质疑的关键前提",
        page=17,
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        4.65,
        "可以回答的问题（定性 / 方法学层面）",
        [
            "本品的 CMI 检测组合在同类产品中所处的位置：涵盖平台新旧、指标宽窄与样本量量级",
            "同类产品在“健康人群预防性接种”场景下，是否同样难以检出统计学显著差异",
            "哪些 assay 升级方向已被同类产品采用并验证：多细胞因子产率、免疫表型、Tfh 功能试验、ELISPOT / AIM",
            "细胞免疫证据在注册申报中应处的定位：探索性终点而非关键有效性依据",
            "以抗-HBs ≥ 10 mIU/mL 为共同锚点，可间接参照体液免疫与细胞免疫的联动关系",
        ],
        bar=RED_DARK,
        body_size=10.0,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        4.65,
        "不能回答的问题（须避免的推断）",
        [
            "不能据本品 ICS 阴性结果推断“本品细胞免疫弱于 HEPLISAV-B”——后者无同场景数据",
            "不能以 CPG 7909 在 HIV 人群的 LPR 阳性结果，反推“HEPLISAV-B 应检出同样阳性”",
            "不能跨研究比较不同平台、不同读值的数值大小（% vs pg/mL vs SI vs CTL 阳性率）",
            "不能以慢性乙肝治疗性动物模型的疗效外推至健康人预防性保护效力",
            "不能以非临床 Th1 偏倚 / IgG2a 结果直接等同于人体抗原特异性 T 细胞应答",
        ],
        bar=GREY,
        body_size=10.0,
    )
    note(
        s,
        "建议口径：对外沟通统一表述为“本品Ⅰ期已建立 CpG 佐剂疫苗细胞免疫评价能力，结果为探索性；"
        "与同类产品的比较限于方法学层面，不构成有效性或优效性主张”。",
        top=5.98,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 18 分隔 04
    divider_page(
        prs,
        blank,
        "04",
        "综合评估与后续建议",
        [
            "方法学与数据质量评价（四项）",
            "注册申报口径建议",
            "后续 assay 升级与研究建议",
            "总体结论",
        ],
        page=18,
    )

    # ================================================================ 19 评价一
    s = content_page(
        prs,
        blank,
        "我们的评价（一）：方法学与数据质量",
        "审慎表述——区分“已证实的事实”与“待验证的预期”",
        page=19,
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        2.30,
        "① 先行性：具备探索价值（已证实）",
        [
            "在原研注册临床资料未见 CMI 数据的前提下，本品Ⅰ期已建立细胞免疫探索性评价体系（ICS + MSD）",
            "这是国内 CpG 佐剂乙肝疫苗较早的一组临床细胞免疫数据，具有方法学建设与机制佐证价值",
        ],
        bar=RED_DARK,
        body_size=10.0,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        2.30,
        "② 灵敏度不足：存在地板效应（已证实）",
        [
            "ICS 报告下限为 0.1%，多数样本中位数落在 0.000%–0.100% 的窄区间，Q1 / Q3 亦高度压缩",
            "同类产品（CPG 7909 的 ⁵¹Cr CTL 试验）同样报告技术困难与数据不完整，提示该限制具有行业共性",
        ],
        bar=GREY,
        body_size=10.0,
    )
    card(
        s,
        0.28,
        3.52,
        6.20,
        2.30,
        "③ 方法学信息不完整（需补充）",
        [
            "CSR 未披露抗原刺激物（全长 HBsAg 或重叠肽池）、刺激浓度与时长",
            "未披露阴性 / 阳性对照设置及阳性判定阈值，影响结果的可重复性与可解释性",
        ],
        bar=GREY,
        body_size=10.0,
    )
    card(
        s,
        6.82,
        3.52,
        6.22,
        2.30,
        "④ 外推性受限（需补充）",
        [
            "每组仅 15 例，且仅覆盖 18–59 岁人群，未纳入 ≥ 60 岁及低应答人群",
            "IP-10 属先天免疫 / 趋化相关标志物，并非抗原特异性 T 细胞应答的直接证据",
        ],
        bar=GREY,
        body_size=10.0,
    )
    note(
        s,
        "整体判断：Ⅰ期细胞免疫数据宜定位为探索性、机制佐证性证据，尚不足以支持任何关于细胞免疫效应的确定性结论。",
        top=6.05,
        left=0.28,
        width=12.75,
    )

    # ================================================================ 20 评价二
    s = content_page(
        prs,
        blank,
        "我们的评价（二）：注册申报口径与后续建议",
        "建议定位：探索性终点，不作为有效性依据",
        page=20,
    )
    card(
        s,
        0.28,
        BODY_TOP,
        6.20,
        2.55,
        "注册申报口径建议",
        [
            "定位为探索性终点，有效性依据仍以体液免疫（抗-HBs 阳转率、GMC）为主",
            "避免使用“原研未开展细胞免疫研究”这类绝对化表述——易被专家质疑；应表述为"
            "“原研注册临床未设 CMI 终点，其细胞免疫证据见于非临床、体外人细胞与治疗性探索研究”",
            "可正面表述“已建立 CpG 佐剂疫苗细胞免疫评价能力”这一方法学建设成果",
            "对阴性 / 无差异结果主动说明 assay 分辨力限制，并援引同类产品的共性表现作为佐证",
        ],
        bar=RED_DARK,
        body_size=9.8,
    )
    card(
        s,
        6.82,
        BODY_TOP,
        6.22,
        2.55,
        "后续研究建议",
        [
            "方法学升级（优先）：参照 BOOST-9 组合，扩展为多细胞因子产率（IFN-γ、TNF-α、IL-2、IL-12、IL-21）+ "
            "免疫表型（PD-1 等）+ Tfh 功能试验；国内可先行引入 ELISPOT / AIM 与多肽池刺激",
            "完善 SOP 与披露：明确刺激抗原、浓度、时长、阴阳性对照与判定阈值，并在 CSR 中完整记录",
            "扩大覆盖：纳入 ≥ 60 岁及低应答人群，提高每组样本量",
            "联动解读：将细胞免疫指标与抗-HBs GMC / 阳转率做相关性分析，形成机制-临床证据链",
            "持续跟踪：BOOST-9（预计 2026–2027）与 TherVacB 结果，可作为重要的外部方法学与结果参照",
        ],
        bar=RED_DARK,
        body_size=9.8,
    )
    panel(
        s,
        0.28,
        3.78,
        12.75,
        2.24,
        "总体结论",
        [
            (
                "1. 检测指标层面：TVAX-009 Ⅰ期设有细胞免疫探索终点（ICS 检测 IL-2 / IFN-γ，MSD 检测 IP-10）；"
                "HEPLISAV-B 注册临床开发中未设 CMI 终点——但其在非临床（Th1 / IgG2a 偏倚、CD4 / CD40L 依赖）、"
                "体外人细胞与治疗性探索研究中确有细胞免疫数据，故不可笼统表述为“原研未做细胞免疫研究”。",
                {"size": 11.5, "bold": True},
            ),
            (
                "2. 检测结果层面：Ⅰ期数据显示 IL-2、IFN-γ 免疫后较免前无明显变化，IP-10 普遍升高但无剂量-效应关系，"
                "且未能与不含 CpG 的对照疫苗区分；横向比较显示同类 CpG 乙肝疫苗在健康人群中同样难以检出显著差异，"
                "故该结果应归因于 assay 分辨力，而非疫苗缺乏细胞免疫效应。",
                {"size": 11.5},
            ),
            (
                "3. 可比性与建议：受检测平台、读值、免疫程序、抗原刺激条件、佐剂分子与免疫场景六重要素限制，"
                "不可进行数值头对头比较；但其方法学设计（多细胞因子产率、免疫表型、Tfh 功能试验、ELISPOT / AIM）"
                "可直接为我所用，建议Ⅱ期起完成 assay 升级并完善方法学披露。",
                {"size": 11.5},
            ),
        ],
        size=11.5,
    )

    prs.save(str(OUT_PPTX))

    # --- sanity check -------------------------------------------------------
    chk = Presentation(str(OUT_PPTX))
    report = [
        f"saved: {OUT_PPTX}",
        f"slides: {len(chk.slides)}",
        f"size: {chk.slide_width.inches:.2f} x {chk.slide_height.inches:.2f} in",
    ]
    W, H = chk.slide_width, chk.slide_height
    for i, sl in enumerate(chk.slides, 1):
        for sh in sl.shapes:
            try:
                r = sh.left + sh.width
                b = sh.top + sh.height
            except (TypeError, AttributeError):
                continue
            if sh.left < -9525 or sh.top < -9525 or r > W + 9525 or b > H + 9525:
                report.append(
                    f"  !! slide {i}: '{sh.shape_type}' out of bounds "
                    f"L={sh.left / 914400:.2f} T={sh.top / 914400:.2f} "
                    f"R={r / 914400:.2f} B={b / 914400:.2f}"
                )
    Path(__file__).with_name("_deck_check.txt").write_text("\n".join(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
