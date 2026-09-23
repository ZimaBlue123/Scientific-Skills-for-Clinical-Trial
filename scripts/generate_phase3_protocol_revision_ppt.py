#!/usr/bin/env python
"""
生成《TVAX-009 Ⅲ期临床方案修订要点（CDE 沟通会前后）》汇报 PPT · V2。

V2 相对 V1 的修订（2026-09-23，按用户反馈）：
  1) P3 总览删除"研究日程表"行（10 项 → 9 项，编号重排）；试验周期只保留整体口径（26 → 20 个月）
  2) 章节转场页大数字 104pt → 48pt，并加几何小图标装饰
  3) P6 新增备选样本量方案表（Power 90% / 85% 组合，给领导留下调口子）
  4) P8 版面重排，嵌入两张Ⅱ期阳转率曲线图（18-59 岁 / ≥60 岁，PPS）
  5) 全局简化 CDE 意见引用（去掉"问题 X / QXX"编号，统一表述为"CDE 沟通会纪要/专家要求"）
  6) P13 文字精简，下半部改为两幅研究流程示意图（旧版 vs 新版采血点对比）
  7) 删除原 P16 / P17
  8) 输出 V2 文件；V1 已备份为 *_V1_backup.pptx

风格基准：review_materials/15-F2F会议/细胞免疫/TVAX-009_细胞免疫_Ⅰ期结果与Ⅲ期设计调整-20260922.pptx
输出：outputs/TVAX-009_Ⅲ期方案修订要点_20260526vs20260922_V2.pptx
"""
import copy
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

BASE = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial"
OUT = os.path.join(BASE, "outputs", "TVAX-009_Ⅲ期方案修订要点_20260526vs20260922_V2.pptx")
FIG_1859 = os.path.join(BASE, "reports", "protocol_diff", "assets", "fig_1859_seropositive_PPS.png")
FIG_60 = os.path.join(BASE, "reports", "protocol_diff", "assets", "fig_60plus_seropositive_PPS.png")

# ---------------- 设计变量 ----------------
FONT = "Arial"
RED = RGBColor(0xC0, 0x00, 0x00)
DARK_RED = RGBColor(0xA1, 0x1C, 0x1D)
PINK = RGBColor(0xE3, 0xB8, 0xB8)
LIGHT_PINK = RGBColor(0xFB, 0xEA, 0xEA)
GRAY = RGBColor(0x59, 0x5F, 0x6B)
BLACK = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SW, SH = 12192000, 6858000
M_LEFT = Emu(256032)
CONTENT_W = SW - M_LEFT * 2
TITLE_L = Emu(420624)
BAR_L, BAR_T, BAR_W, BAR_H = Emu(228600), Emu(137160), Emu(82296), Emu(402336)
RULE_T = Emu(859536)
FOOT_T = Emu(6419088)
FOOTER_TEXT = "TVAX-009 Ⅲ期临床方案修订要点｜V1.0（2026-05-26）vs 修订版（2026-09-22）"


# ---------------- 基础工具 ----------------
def _style_run(run, size=10, bold=False, color=BLACK, font=FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    latin = rPr.find(qn("a:latin"))
    if latin is None:
        from pptx.oxml import parse_xml
        from pptx.oxml.ns import nsdecls
        latin = parse_xml('<a:latin %s typeface="%s"/>' % (nsdecls("a"), font))
        rPr.append(latin)
    else:
        latin.set("typeface", font)
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = copy.deepcopy(latin)
        ea.tag = qn("a:ea")
        latin.addnext(ea)
    ea.set("typeface", font)
    return run


def textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP, wrap=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    return tf


def add_para(tf, text, size=10, bold=False, color=BLACK, first=False, space_after=0,
             align=PP_ALIGN.LEFT, line=None, bullet_char=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    if space_after:
        p.space_after = Pt(space_after)
    if line:
        p.line_spacing = line
    if bullet_char:
        p.text = ""
        r0 = p.add_run()
        r0.text = bullet_char + " "
        _style_run(r0, size, bold, color)
    r = p.add_run()
    r.text = text
    _style_run(r, size, bold, color)
    return p


def rect(slide, left, top, width, height, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    sp = slide.shapes.add_shape(shape, left, top, width, height)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(0.75)
    sp.shadow.inherit = False
    return sp


def _kill_table_style(table):
    tblPr = table._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    tblPr.set("firstCol", "0")


def add_table(slide, left, top, width, height, data, col_widths=None,
              header=True, font_size=9.5, header_size=9.5,
              header_fill=DARK_RED, body_alt=LIGHT_PINK, aligns=None):
    rows, cols = len(data), len(data[0])
    gt = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = gt.table
    _kill_table_style(table)
    if col_widths:
        total = sum(col_widths)
        for i, w in enumerate(col_widths):
            table.columns[i].width = Emu(int(width * w / total))
    for ri, row in enumerate(data):
        for ci, cell_text in enumerate(row):
            cell = table.cell(ri, ci)
            cell.margin_left = Emu(68580)
            cell.margin_right = Emu(68580)
            cell.margin_top = Emu(22860)
            cell.margin_bottom = Emu(22860)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            is_head = header and ri == 0
            cell.fill.solid()
            if is_head:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = body_alt if (ri % 2 == 0) else WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            align = PP_ALIGN.LEFT
            if aligns and aligns[ci] == "c":
                align = PP_ALIGN.CENTER
            add_para(tf, str(cell_text), size=header_size if is_head else font_size,
                     bold=is_head, color=WHITE if is_head else BLACK, first=True, align=align,
                     line=1.05)
    return table


def card(slide, left, top, width, height, title, lines, title_size=11.5, body_size=9.5,
         head_fill=DARK_RED, body_fill=LIGHT_PINK, title_color=WHITE, body_color=BLACK):
    rect(slide, left, top, width, height, fill=body_fill)
    head_h = Emu(310896)
    rect(slide, left, top, width, head_h, fill=head_fill)
    tf = textbox(slide, left + Emu(109728), top + Emu(54864), width - Emu(219456), head_h)
    add_para(tf, title, size=title_size, bold=True, color=title_color, first=True)
    tf2 = textbox(slide, left + Emu(137160), top + head_h + Emu(91440),
                  width - Emu(274320), height - head_h - Emu(137160))
    for i, ln in enumerate(lines):
        add_para(tf2, ln, size=body_size, bold=False, color=body_color, first=(i == 0),
                 space_after=4, line=1.15, bullet_char="·")
    return tf2


def content_slide(prs, title, subtitle, page_no, footer=FOOTER_TEXT):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, BAR_L, BAR_T, BAR_W, BAR_H, fill=RED)
    tf = textbox(slide, TITLE_L, Emu(137160), CONTENT_W - Emu(192024), Emu(457200))
    add_para(tf, title, size=21, bold=True, color=BLACK, first=True)
    if subtitle:
        tf2 = textbox(slide, TITLE_L, Emu(585216), CONTENT_W - Emu(192024), Emu(256032))
        add_para(tf2, subtitle, size=10.5, bold=False, color=GRAY, first=True)
    rect(slide, BAR_L, RULE_T, SW - BAR_L * 2, Emu(18288), fill=RED)
    ft = textbox(slide, M_LEFT, FOOT_T, Emu(8229600), Emu(237744))
    add_para(ft, footer, size=8, color=GRAY, first=True)
    pn = textbox(slide, Emu(11247120), FOOT_T, Emu(713232), Emu(237744))
    add_para(pn, str(page_no), size=9, bold=True, color=RED, first=True, align=PP_ALIGN.RIGHT)
    return slide


def section_slide(prs, number, title, points, page_no):
    """章节转场页：数字缩小至 48pt，左侧加几何小图标装饰。"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, BAR_L, BAR_T, BAR_W, BAR_H, fill=RED)
    tf = textbox(slide, TITLE_L, Emu(137160), CONTENT_W - Emu(192024), Emu(457200))
    add_para(tf, title, size=21, bold=True, color=BLACK, first=True)
    rect(slide, BAR_L, RULE_T, SW - BAR_L * 2, Emu(18288), fill=RED)
    # 几何小图标：浅粉菱形 + 红色菱形错位叠加
    rect(slide, M_LEFT, Emu(1350000), Emu(430000), Emu(430000), fill=PINK, shape=MSO_SHAPE.DIAMOND)
    rect(slide, M_LEFT + Emu(190000), Emu(1540000), Emu(430000), Emu(430000), fill=RED, shape=MSO_SHAPE.DIAMOND)
    ntf = textbox(slide, M_LEFT + Emu(780000), Emu(1180000), Emu(2400000), Emu(1000000))
    add_para(ntf, number, size=48, bold=True, color=RED, first=True)
    ctf = textbox(slide, M_LEFT, Emu(2350000), Emu(6200000), Emu(550000))
    add_para(ctf, "本章核心", size=13, bold=True, color=DARK_RED, first=True)
    rect(slide, M_LEFT, Emu(2830000), Emu(1500000), Emu(36576), fill=DARK_RED)
    ptf = textbox(slide, M_LEFT, Emu(3050000), CONTENT_W, Emu(2900000))
    for i, p in enumerate(points):
        add_para(ptf, p, size=11.5, color=BLACK, first=(i == 0), space_after=10,
                 line=1.2, bullet_char="·")
    ft = textbox(slide, M_LEFT, FOOT_T, Emu(8229600), Emu(237744))
    add_para(ft, FOOTER_TEXT, size=8, color=GRAY, first=True)
    pn = textbox(slide, Emu(11247120), FOOT_T, Emu(713232), Emu(237744))
    add_para(pn, str(page_no), size=9, bold=True, color=RED, first=True, align=PP_ALIGN.RIGHT)
    return slide


def source_note(slide, text, top=Emu(5230368)):
    rect(slide, M_LEFT, top, CONTENT_W, Emu(54864), fill=LIGHT_PINK)
    tf = textbox(slide, M_LEFT, top + Emu(91440), CONTENT_W, Emu(1000000))
    add_para(tf, text, size=8, color=GRAY, first=True, line=1.15)
    return tf


def schedule_card(slide, left, top, width, height, title, rows, head_fill=DARK_RED):
    """研究流程示意图卡片：rows = [(行标签, [(时点名, 接种bool, 采血bool, 主终点bool), ...]), ...]"""
    rect(slide, left, top, width, height, fill=WHITE, line=PINK)
    head_h = Emu(310896)
    rect(slide, left, top, width, head_h, fill=head_fill)
    tf = textbox(slide, left + Emu(109728), top + Emu(54864), width - Emu(219456), head_h)
    add_para(tf, title, size=11, bold=True, color=WHITE, first=True)
    axis_l = left + Emu(1250000)
    axis_r = left + width - Emu(160000)
    axis_w = axis_r - axis_l
    row_h = Emu(830000)
    for ri, (label, pts) in enumerate(rows):
        ry = top + head_h + Emu(60000) + ri * row_h
        lt = textbox(slide, left + Emu(110000), ry, Emu(1100000), Emu(300000))
        add_para(lt, label, size=8.5, bold=True, color=BLACK, first=True)
        axis_y = ry + Emu(430000)
        ln = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, axis_l, axis_y, axis_w, Emu(12700))
        ln.fill.solid(); ln.fill.fore_color.rgb = PINK; ln.line.fill.background(); ln.shadow.inherit = False
        n = len(pts)
        span = axis_w - Emu(300000)
        tri_d, dot_d = Emu(110000), Emu(110000)
        for pi, (name, vac, blood, star) in enumerate(pts):
            x = axis_l + Emu(150000) + int(span * pi / max(n - 1, 1))
            if vac:
                t = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,
                                           x - tri_d // 2, axis_y - Emu(170000), tri_d, tri_d)
                t.fill.solid(); t.fill.fore_color.rgb = RED; t.line.fill.background(); t.shadow.inherit = False
            if blood:
                d = Emu(150000) if star else dot_d
                c = slide.shapes.add_shape(MSO_SHAPE.OVAL, x - d // 2, axis_y + Emu(60000), d, d)
                c.fill.solid(); c.fill.fore_color.rgb = RED if star else GRAY
                if star:
                    c.line.color.rgb = WHITE; c.line.width = Pt(1)
                else:
                    c.line.fill.background()
                c.shadow.inherit = False
            lt2 = textbox(slide, x - Emu(300000), axis_y + Emu(230000), Emu(600000), Emu(200000))
            add_para(lt2, name + ("★" if star else ""), size=7, bold=star,
                     color=RED if star else GRAY, first=True, align=PP_ALIGN.CENTER)


# ---------------- 页面内容 ----------------
def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH

    # --- P1 封面 ---
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, SW, Emu(256032), fill=RED)
    rect(s, 0, Emu(6601968), SW, Emu(256032), fill=RED)
    tf = textbox(s, Emu(868680), Emu(1426464), Emu(10451592), Emu(566928))
    add_para(tf, "重组乙型肝炎疫苗（汉逊酵母，CpG 和铝佐剂）", size=21, bold=True, color=RED, first=True)
    tf = textbox(s, Emu(868680), Emu(2135184), Emu(10451592), Emu(900000))
    add_para(tf, "Ⅲ期临床方案修订要点：CDE 沟通会前后的设计变化", size=34, bold=True, color=BLACK, first=True)
    tf = textbox(s, Emu(868680), Emu(3408144), Emu(10451592), Emu(365760))
    add_para(tf, "研究假设  ·  终点体系  ·  细胞免疫  ·  访视与安全性  ·  样本量", size=12.5, bold=True, color=GRAY, first=True)
    rect(s, Emu(4956048), Emu(3986784), Emu(2286000), Emu(32004), fill=DARK_RED)
    tf = textbox(s, Emu(868680), Emu(4261104), Emu(10451592), Emu(650000))
    add_para(tf, "YDSWX（TVAX-009）-004 ｜ 方案 V1.0（2026-05-26，会前递交） → 方案摘要修订版（2026-09-22，根据 CDE 沟通会意见调整）",
             size=10.5, color=GRAY, first=True, line=1.2)
    tf = textbox(s, Emu(1975104), Emu(5230368), Emu(8229600), Emu(1005840))
    add_para(tf, "远大赛威信生命科学（南京）有限公司", size=12.5, bold=True, color=BLACK, first=True, align=PP_ALIGN.CENTER)
    add_para(tf, "2026 年 09 月", size=12.5, bold=True, color=BLACK, align=PP_ALIGN.CENTER, space_after=6)

    # --- P2 目录 ---
    s = content_slide(prs, "汇报内容", "以设计层面重大调整为主线，附可供挑选的次要修订", 2)
    cards = [
        ("01  研究假设与样本量", ["60 岁及以上：非劣效 → 优效", "总样本量 2,960 → 3,380 例", "新增安全性样本量考虑"]),
        ("02  免疫原性终点", ["主要终点时点：首剂后 7 个月 → 全程接种后 1 个月", "新增全程接种后 2 个月", "持久性终点改为全程接种后 6/12 个月"]),
        ("03  细胞免疫", ["Ⅲ期由“无”到“有”，增设探索性终点", "细胞免疫 1 组 100 例（ELISpot＋ICS）", "细胞免疫 2 组 25 例（pDC 机制层）"]),
        ("04  访视、安全性与周期", ["新增预筛选 V0 与 D1／D3 访视", "AESI 增至 11 项、随访延至 12 个月", "周期 26 → 20 个月，取消期中分析"]),
    ]
    w = Emu(5669280)
    for i, (t, lines) in enumerate(cards):
        left = M_LEFT if i % 2 == 0 else Emu(6236208)
        top = Emu(1097280) if i < 2 else Emu(3108960)
        card(s, left, top, w, Emu(1850000), t, lines)

    # --- P3 总览（9 项；周期只保留整体口径） ---
    s = content_slide(prs, "修订总览：9 项设计层面重大调整",
                      "按对注册路径与试验执行的影响程度排序；第 4 项为最核心变更", 3)
    data = [["#", "调整维度", "旧版 V1.0（2026-05-26）", "新版（2026-09-22）", "性质"],
            ["1", "老年人群检验假设", "非劣效，Δ = -5%", "优效，优效界值 0%", "假设变更"],
            ["2", "研究题目／总体设计", "随机、盲法、阳性对照、非劣效设计", "删除“非劣效”；18-59 岁非劣、≥60 岁优效", "表述分层"],
            ["3", "总样本量", "2,960 例", "3,380 例（+420，+14.2%）", "扩大"],
            ["4", "主要终点评价时点", "首剂接种后 7 个月", "全程接种后 1 个月", "口径变更"],
            ["5", "次要／持久性终点", "首剂后 7 个月＋首剂后 12／18／24 个月", "全程接种后 1／2／6／12 个月＋首剂后 1／6 个月", "体系重构"],
            ["6", "细胞免疫", "未设置", "增设探索性终点（1 组 100 例、2 组 25 例）", "新增"],
            ["7", "体液免疫采血时点", "首剂后 1／6／7／12／24 个月（按程序补采）", "首剂后 1／6 个月＋全程接种后 1／2／6／12 个月", "口径变更"],
            ["8", "安全性观察", "SAE／AESI 至全程接种后 6 个月", "至全程接种后 12 个月；AESI 8 → 11 项", "强化"],
            ["9", "试验周期与分析策略", "约 26 个月；首次＋末次两次分析",
             "约 20 个月（首例入组至末例完成末次访视）；删除两次分析安排", "缩短／重写"]]
    add_table(s, M_LEFT, Emu(1097280), CONTENT_W, Emu(4200000), data,
              col_widths=[4, 20, 30, 32, 14], font_size=9, header_size=9.5,
              aligns=["c", "l", "l", "l", "c"])
    source_note(s, "依据：CDE Ⅲ期临床试验启动前沟通会（EoP2，2026-09-16 面对面 + 09-18 线上）会议纪要；新版方案摘要修订痕迹。")

    # --- P4 章节 01 ---
    section_slide(prs, "01", "研究假设、检验策略与样本量", [
        "60 岁及以上人群：非劣效 → 优效（优效界值 0%），对照组阳转率假设由 95% 下调至 90%",
        "老年每组入组 520 → 730 例；总样本量 2,960 → 3,380 例",
        "研究题目与总体设计删除“非劣效”字样，改为按年龄队列分层表述",
        "新增安全性样本量考虑：试验组 2,010 例",
    ], 4)

    # --- P5 老年检验假设 ---
    s = content_slide(prs, "调整 ①：60 岁及以上人群由“非劣效”改为“优效”",
                      "检验类型、界值与样本量假设同步改写；该人群免疫程序维持 0,1,6 月三剂头对头", 5)
    card(s, M_LEFT, Emu(1097280), Emu(5669280), Emu(1900000), "旧版：非劣效",
         ["检验类型：非劣效；界值 Δ = -5%", "假设阳转率：试验组 ≥95%、对照组 ≥95%",
          "每组需 441 例 → 入组 520 例（合计 1,040）", "依据：以“2 剂达到 3 剂水平”为注册路径"],
         head_fill=GRAY)
    card(s, Emu(6236208), Emu(1097280), Emu(5669280), Emu(1900000), "新版：优效",
         ["检验类型：优效；优效界值 0%（率差双侧 95% CI 下限 > 0%）",
          "假设阳转率：试验组 ≥95%、对照组 ≥90%",
          "每组需 621 例 → 入组 730 例（合计 1,460）",
          "α 单侧 0.025，把握度 90%，不可评价率 15%"],
         head_fill=RED)
    data = [["检验参数", "旧版", "新版"],
            ["检验类型", "非劣效", "优效"],
            ["界值", "Δ = -5%（率差 95%CI 下限 > -5%）", "0%（率差 95%CI 下限 > 0%）"],
            ["阳转率假设", "试验 ≥95% ／ 对照 ≥95%", "试验 ≥95% ／ 对照 ≥90%"],
            ["每组所需例数／入组例数", "441 ／ 520", "621 ／ 730"],
            ["该队列合计", "1,040 例", "1,460 例"]]
    add_table(s, M_LEFT, Emu(3175000), CONTENT_W, Emu(1900000), data,
              col_widths=[26, 34, 40], font_size=9.5, aligns=["l", "c", "c"])
    tf = textbox(s, M_LEFT, Emu(5200000), CONTENT_W, Emu(1100000))
    add_para(tf, "依据与口径提示", size=11, bold=True, color=DARK_RED, first=True)
    add_para(tf, "· 依据：CDE 沟通会纪要明确——“如果 60 岁以上人群做三剂接种要优效于阳性对照”。",
             size=9.5, color=BLACK, space_after=3, line=1.15)
    add_para(tf, "· 数据支撑（Ⅱ期）：全程免后 1 个月阳转率 100.00% vs 91.55%（P=0.0280）；全程免后 6 个月 98.55% vs 85.92%（P=0.0055）。",
             size=9.5, color=BLACK, space_after=3, line=1.15)
    add_para(tf, "· 口径提示：专家面对面会后的初步方向为“老年改 2 剂程序、不主张优效”，新版最终采用“3 剂头对头＋优效检验”，对外材料须统一到 CDE 会议纪要口径。",
             size=9.5, color=RED, line=1.15)

    # --- P6 样本量 + 备选方案 ---
    s = content_slide(prs, "调整 ②③：总样本量 2,960 → 3,380 例（附备选方案）",
                      "18-59 岁维持不变；增量全部来自 60 岁及以上队列；如需压缩总样本量，可通过下调把握度实现", 6)
    nums = [("3,380", "新版总样本量", "较旧版 2,960 例 +420 例（+14.2%）"),
            ("730 × 2", "60 岁及以上", "旧版 520 × 2 = 1,040 例 → 1,460 例"),
            ("2,010", "试验组例数", "用于安全性观察（0.1% AE 检出）")]
    for i, (big, lab, sub) in enumerate(nums):
        left = M_LEFT + Emu(int(i * 3920000))
        rect(s, left, Emu(1060000), Emu(3760000), Emu(950000), fill=LIGHT_PINK)
        rect(s, left, Emu(1060000), Emu(3760000), Emu(45720), fill=RED)
        tf = textbox(s, left + Emu(137160), Emu(1150000), Emu(3500000), Emu(430000))
        add_para(tf, big, size=22, bold=True, color=RED, first=True)
        tf = textbox(s, left + Emu(137160), Emu(1580000), Emu(3500000), Emu(400000))
        add_para(tf, lab, size=10, bold=True, color=BLACK, first=True)
        add_para(tf, sub, size=8.5, color=GRAY, line=1.05)
    data = [["年龄队列", "分组与比例", "旧版每组／合计", "新版每组／合计", "变化"],
            ["18-59 岁", "0,1月 : 0,2月 : 对照 = 1:1:1", "640／1,920", "640／1,920", "不变"],
            ["60 岁及以上", "试验 : 对照 = 1:1", "520／1,040", "730／1,460", "+420"],
            ["合计", "—", "—／2,960", "—／3,380", "+420"]]
    add_table(s, M_LEFT, Emu(2130000), CONTENT_W, Emu(1150000), data,
              col_widths=[18, 34, 20, 20, 12], font_size=9, aligns=["l", "l", "c", "c", "c"])
    # 备选方案表
    tf = textbox(s, M_LEFT, Emu(3400000), CONTENT_W, Emu(280000))
    add_para(tf, "备选样本量方案（如集团认为总样本量偏高，可下调把握度；检验参数不变）", size=11, bold=True, color=DARK_RED, first=True)
    data = [["备选方案", "18-59 岁（非劣，Δ=-5%）", "60 岁及以上（优效，界值 0%）", "总样本量", "较方案 A"],
            ["方案 A（现行，推荐）", "把握度 90%：640×3 = 1,920", "把握度 90%：730×2 = 1,460", "3,380", "—"],
            ["方案 B（下调老年把握度）", "把握度 90%：640×3 = 1,920", "把握度 85%：630×2 = 1,260", "3,180", "-200"],
            ["方案 C（两年龄层均下调）", "把握度 85%：570×3 = 1,710", "把握度 85%：630×2 = 1,260", "2,970", "-410"]]
    add_table(s, M_LEFT, Emu(3730000), CONTENT_W, Emu(1500000), data,
              col_widths=[24, 27, 29, 12, 10], font_size=9, aligns=["l", "c", "c", "c", "c"])
    tf = textbox(s, M_LEFT, Emu(5330000), CONTENT_W, Emu(1000000))
    add_para(tf, "· 把握度指试验整体把握度（Global Power）；每次检验的把握度按 Bonferroni 校正换算（两年龄层单终点策略）。α 单侧 0.025、阳转率与界值假设、不可评价率 15% 均保持不变。",
             size=9, color=BLACK, first=True, space_after=3, line=1.15)
    add_para(tf, "· 数值取自《Sample Size-009 phase3-单终点_非劣 vs 优效》2026-09-21 updated。新增安全性样本量考虑（试验组 2,010 例）依据：CDE 沟通会纪要——样本量须兼顾安全性观察，至少能观察到偶见不良反应。",
             size=9, color=GRAY, line=1.15)

    # --- P7 章节 02 ---
    section_slide(prs, "02", "免疫原性终点体系", [
        "主要终点：由“首剂接种后 7 个月”改为“全程接种后 1 个月”——本次最核心变更",
        "试验组评价时点实质提前（0,1 月组 M2、0,2 月组 M3），对照组维持 M7",
        "新增全程接种后 2 个月；持久性由首剂后 12／18／24 个月改为全程接种后 6／12 个月",
        "首剂后 1、6 个月由探索性上调为次要终点",
    ], 7)

    # --- P8 主要终点 + II 期数据图 ---
    s = content_slide(prs, "调整 ④（核心）：主要终点时点改为“全程接种后 1 个月”",
                      "比较口径由“同一日历时点、不同免疫阶段”改为“各自全程免疫后同一相对时点”——既是 CDE 要求，也有Ⅱ期数据支撑", 8)
    data = [["组别", "接种程序", "旧版主要终点", "新版主要终点", "是否变化"],
            ["18-59 岁 0,1 月试验组", "0、1 月（2 剂）", "首剂后 7 个月（M7）", "全程接种后 1 个月 = M2", "提前 5 个月"],
            ["18-59 岁 0,2 月试验组", "0、2 月（2 剂）", "首剂后 7 个月（M7）", "全程接种后 1 个月 = M3", "提前 4 个月"],
            ["对照组（18-59 岁）", "0、1、6 月（3 剂）", "首剂后 7 个月（M7）", "全程接种后 1 个月 = M7", "不变"],
            ["≥60 岁试验组／对照组", "0、1、6 月（3 剂）", "首剂后 7 个月（M7）", "全程接种后 1 个月 = M7", "不变"]]
    add_table(s, M_LEFT, Emu(1060000), CONTENT_W, Emu(1300000), data,
              col_widths=[24, 18, 22, 26, 14], font_size=9,
              aligns=["l", "c", "c", "c", "c"])
    # 两张 II 期图（图卡）
    figs = [
        (M_LEFT, FIG_1859, "18-59 岁免前阴性人群接种后抗-HBs 阳转率折线图（PPS，Ⅱ期）", 591, 279),
        (Emu(6236208), FIG_60, "≥60 岁免前阴性人群接种后抗-HBs 阳转率折线图（PPS，Ⅱ期）", 940, 467),
    ]
    for left, path, cap, iw, ih in figs:
        cw = Emu(5669280)
        card_top = Emu(2500000)
        rect(s, left, card_top, cw, Emu(3050000), fill=WHITE, line=PINK)
        rect(s, left, card_top, cw, Emu(274320), fill=DARK_RED)
        tf = textbox(s, left + Emu(109728), card_top + Emu(41000), cw - Emu(219456), Emu(240000))
        add_para(tf, cap, size=9.5, bold=True, color=WHITE, first=True)
        disp_w = cw - Emu(320000)
        disp_h = int(disp_w * ih / iw)
        if disp_h > Emu(2450000):
            disp_h = Emu(2450000)
            disp_w = int(disp_h * iw / ih)
        s.shapes.add_picture(path, left + (cw - disp_w) // 2, card_top + Emu(360000),
                             width=disp_w, height=disp_h)
    tf = textbox(s, M_LEFT, Emu(5650000), CONTENT_W, Emu(750000))
    add_para(tf, "· 图中可见：18-59 岁 2 剂程序于 M2／M3 即达约 98%–100% 阳转率，与对照组 3 剂峰值（M7 97.22%）相当；≥60 岁试验组各时点均高于对照（全程免后 1 个月 100.00% vs 91.55%）——为Ⅲ期主要终点时点调整提供免疫应答规律的数据依据。",
             size=9, color=BLACK, first=True, space_after=3, line=1.15)
    add_para(tf, "· 依据：CDE 沟通会纪要要求主要终点评价时间点设置为全程免疫后相同时间点的阳转率（可选 1 或 2 个月，不同免疫程序的时间节点须保持一致）；需同步在 SAP 中重新界定估计目标、伴发事件策略与缺失数据处理。",
             size=9, color=RED, line=1.15)

    # --- P9 次要终点 ---
    s = content_slide(prs, "调整 ⑤：次要终点与免疫持久性终点体系重构",
                      "时点口径统一为“全程接种后”，并回应专家对免疫持久性的关切", 9)
    data = [["终点项", "旧版 V1.0", "新版（2026-09-22）", "性质"],
            ["全程接种后 1 个月", "（主要终点时点）GMC、SPR-100", "各组 GMC、SPR-100", "保留"],
            ["全程接种后 2 个月", "未设", "各组阳转率、GMC、SPR-100", "新增"],
            ["首剂后 1、6 个月", "探索性终点", "上调为次要终点（各组）", "层级上调"],
            ["全程接种后 6 个月", "仅 0,2 月组与各 0,1,6 月组", "各组阳转率、GMC、SPR-100", "扩至各组"],
            ["全程接种后 12 个月", "未设（旧为首剂后 18 个月）", "各组阳转率、GMC、SPR-100", "新增"],
            ["首剂后 12／18／24 个月", "探索性终点（按程序分别描述）", "取消", "删除"]]
    add_table(s, M_LEFT, Emu(1097280), CONTENT_W, Emu(2100000), data,
              col_widths=[22, 30, 32, 16], font_size=9.5, aligns=["l", "l", "l", "c"])
    card(s, M_LEFT, Emu(3400000), Emu(5669280), Emu(1250000), "新版次要终点（体液免疫）完整口径",
         ["全程接种后 1 个月：GMC、SPR-100", "全程接种后 2／6／12 个月：阳转率、GMC、SPR-100",
          "首剂接种后 1／6 个月：阳转率、GMC、SPR-100"])
    card(s, Emu(6236208), Emu(3400000), Emu(5669280), Emu(1250000), "探索性终点（体液免疫）",
         ["新增：有／无乙肝疫苗接种史人群各时间点阳转率、GMC、SPR-100",
          "依据：CDE 沟通会纪要——人群聚焦无接种史成人，接种史作预设亚组／探索性分析",
          "接种史仅作基线信息与探索性分析变量，不作分组因素"])
    source_note(s, "依据：CDE 沟通会纪要——安全性与免疫持久性随访至全程免疫后 12 个月；免疫持久性（全程接种后 12 个月）由探索性上调为次要终点。")

    # --- P10 章节 03 ---
    section_slide(prs, "03", "细胞免疫：Ⅲ期由“无”到“有”", [
        "旧版方案全文未设细胞免疫终点；新版在探索性终点下增设，为本次全新内容",
        "细胞免疫 1 组 100 例：ELISpot（IFN-γ）＋ ICS（CD4⁺／CD8⁺ 多功能细胞因子）",
        "细胞免疫 2 组 25 例：pDC 活化表型（流式）＋ IFN-γ／IP-10／IL-6，用于机制探索",
        "计划在一个研究现场设置亚组；两组互斥入组，首次纳入 ≥60 岁人群",
    ], 10)

    # --- P11 细胞免疫设计 ---
    s = content_slide(prs, "调整 ⑥：细胞免疫 1 组与 2 组的设置",
                      "相对Ⅰ期的升级：由 3 项指标扩展为 ELISpot ＋ 多功能 ICS，并新增 pDC–Ⅰ型干扰素轴机制层", 11)
    data = [["队列", "入组方式与例数", "检测指标", "检测方法", "采血时点"],
            ["细胞免疫 1 组\n（抗原特异性应答）",
             "18-59 岁入组前 60 例 ＋ ≥60 岁入组前 40 例\n共 100 例",
             "抗原特异性 T 细胞分泌 IFN-γ；表达 ≥2 种活化标志物（IFN-γ、TNF-α、IL-2）的 CD4⁺／CD8⁺ T 细胞比例",
             "ELISpot（酶联免疫斑点）\nICS（胞内细胞因子染色）",
             "免前、首剂后第 8 天、末剂前、全程接种后第 8 天、首剂后 6 个月"],
            ["细胞免疫 2 组\n（固有免疫与机制）",
             "18-59 岁第 61–75 例 ＋ ≥60 岁第 41–50 例\n共 25 例",
             "表达活化标志物（CD123、BDCA-2/4、HLA-DR、CD80/86）的 pDC 细胞比例；IFN-γ、IP-10、IL-6",
             "流式细胞术\n（细胞因子检测方法待定）",
             "免前、首剂后第 1 天、第 3 天、第 8 天"]]
    add_table(s, M_LEFT, Emu(1097280), CONTENT_W, Emu(2000000), data,
              col_widths=[16, 20, 30, 16, 18], font_size=9, header_size=9.5)
    card(s, M_LEFT, Emu(3250000), Emu(3760000), Emu(1500000), "与Ⅰ期的对照",
         ["Ⅰ期：ICS（IL-2、IFN-γ）＋ MSD（IP-10），60 例 18-59 岁",
          "Ⅲ期：ELISpot ＋ 多功能 ICS ＋ pDC 机制层",
          "样本 60 → 100 例（1 组），首次纳入 ≥60 岁"])
    card(s, Emu(3937000), Emu(3250000), Emu(3760000), Emu(1500000), "依据（CDE 沟通会专家要求）",
         ["Ⅲ期增设细胞免疫研究终点，采血时点较Ⅰ期更密集",
          "扩大细胞因子的检测覆盖范围，形成免疫图谱",
          "检测基于实际使用的混合后制剂（临用前混合）评价"], head_fill=RED)
    card(s, Emu(7874000), Emu(3250000), Emu(3760000), Emu(1500000), "待定与实施要点",
         ["细胞免疫采血量：XX~XX mL（待定）", "细胞因子检测方法：XX 方法（待定）",
          "判定阈值与应答者定义须在揭盲前锁定"])
    source_note(s, "来源：新版方案摘要（痕迹版）·研究终点与研究设计章节；《TVAX-009 细胞免疫：Ⅰ期结果与Ⅲ期设计调整》2026-09-22。Ⅰ期结论为探索性描述，不作为有效性依据。")

    # --- P12 章节 04 ---
    section_slide(prs, "04", "访视流程、安全性与试验周期", [
        "新增预筛选访视 V0（D-90），并新增 D1／D3 早期访视服务细胞免疫",
        "体液免疫采血时点统一为“全程接种后”口径；单次采血量 3–4 mL → 4–5 mL",
        "SAE／AESI 与妊娠事件收集延长至全程接种后 12 个月；AESI 由 8 项增至 11 项",
        "试验周期 26 → 20 个月；删除“首次＋末次”两次分析安排",
    ], 12)

    # --- P13 日程表：精简文字 + 流程图对比 ---
    s = content_slide(prs, "调整 ⑦：研究日程表与采血点变化（流程图对比）",
                      "新增预筛选 V0 与 D1／D3 早期访视；体液免疫采血时点整体改为“全程接种后”口径", 13)
    data = [["要素", "旧版 V1.0", "新版（2026-09-22）"],
            ["预筛选访视", "无（V1 起，D-1～D0 筛选）", "新增 V0（D-90）：签署预筛选知情同意书，采血 4.0~5.0 mL 做乙肝两对半定量"],
            ["早期访视（细胞免疫）", "无", "新增 V2（D1）、V3（D3），窗口 ±4 小时"],
            ["采血量／筛查互认", "3.0~4.0 mL；认可协议医院 14 天内筛查结果", "4.0~5.0 mL；删除互认表述，改由预筛选／筛选阶段现场采血"]]
    add_table(s, M_LEFT, Emu(1060000), CONTENT_W, Emu(1150000), data,
              col_widths=[16, 34, 50], font_size=8.5)
    # 流程图两卡
    old_rows = [
        ("0,1 月程序", [("D0", 1, 1, 1), ("M1", 1, 1, 0), ("M2", 0, 1, 0), ("M6", 0, 1, 0),
                       ("M7", 0, 1, 0), ("M12", 0, 1, 0), ("M24", 0, 1, 0)]),
        ("0,2 月程序", [("D0", 1, 1, 1), ("M1", 0, 1, 0), ("M2", 1, 1, 0), ("M3", 0, 1, 0),
                       ("M6", 0, 1, 0), ("M7", 0, 1, 0), ("M8", 0, 1, 0), ("M12", 0, 1, 0), ("M24", 0, 1, 0)]),
        ("0,1,6 月程序", [("D0", 1, 1, 1), ("M1", 1, 1, 0), ("M6", 1, 1, 0), ("M7", 0, 1, 0),
                         ("M12", 0, 1, 0), ("M18", 0, 1, 0), ("M24", 0, 1, 0)]),
    ]
    new_rows = [
        ("0,1 月程序", [("D0", 1, 1, 0), ("M1", 1, 1, 0), ("M2", 1, 1, 1), ("M3", 0, 1, 0),
                       ("M6", 0, 1, 0), ("M7", 0, 1, 0), ("M13", 0, 1, 0)]),
        ("0,2 月程序", [("D0", 1, 1, 0), ("M1", 0, 1, 0), ("M2", 1, 1, 0), ("M3", 0, 1, 1),
                       ("M4", 0, 1, 0), ("M6", 0, 1, 0), ("M8", 0, 1, 0), ("M14", 0, 1, 0)]),
        ("0,1,6 月程序", [("D0", 1, 1, 0), ("M1", 1, 1, 0), ("M6", 1, 1, 0), ("M7", 0, 1, 1),
                         ("M8", 0, 1, 0), ("M12", 0, 1, 0), ("M18", 0, 1, 0)]),
    ]
    cw = Emu(5669280)
    schedule_card(s, M_LEFT, Emu(2380000), cw, Emu(2950000), "旧版 V1.0：体液免疫采血时点（主终点均为 M7）",
                  old_rows, head_fill=GRAY)
    schedule_card(s, Emu(6236208), Emu(2380000), cw, Emu(2950000),
                  "新版 2026-09-22：主终点改为各组“全程接种后 1 个月”", new_rows, head_fill=RED)
    tf = textbox(s, M_LEFT, Emu(5420000), CONTENT_W, Emu(900000))
    add_para(tf, "图例：▲ 接种  ● 体液免疫采血  ●（红色大点）＋★ 主要终点采血时点；末次访视：旧版均为 M24 → 新版 0,1 月 M13、0,2 月 M14、0,1,6 月 M18（全程接种后 12 个月）。细胞免疫时点（D1／D3／D8、末剂前、末剂后第 8 天等）见第 11 页，图中未重复展示。",
             size=8.5, color=GRAY, first=True, line=1.15)

    # --- P14 安全性 ---
    s = content_slide(prs, "调整 ⑧：安全性观察强化",
                      "随访窗口延长、AESI 清单扩充、主动随访加密，回应复合佐剂系统的首次应用", 14)
    data = [["项目", "旧版 V1.0", "新版（2026-09-22）", "变化性质"],
            ["SAE／AESI 收集窗口", "首剂接种至全程接种后 6 个月", "首剂接种至全程接种后 12 个月", "延长"],
            ["妊娠事件收集", "全程接种后 6 个月内", "全程接种后 12 个月内", "延长"],
            ["AESI 清单", "8 项", "11 项（新增 3 项）", "扩充"],
            ["主动安全性随访", "按固定访视区间随访（如 V5~V6 至少 3 次）", "末次现场访视后至少每月一次（微信／电话）", "加密"],
            ["样本量的安全性论证", "未设", "新增：试验组 2,010 例，可观察 ≥0.1% 的 AE", "新增"]]
    add_table(s, M_LEFT, Emu(1097280), CONTENT_W, Emu(1900000), data,
              col_widths=[18, 30, 32, 16], font_size=9.5, aligns=["l", "l", "l", "c"])
    card(s, M_LEFT, Emu(3200000), Emu(5669280), Emu(1300000), "AESI 清单原有 8 项",
         ["肉芽肿伴多血管炎、扁平苔藓、吉兰-巴雷综合征", "毒性弥漫性甲状腺肿（Graves 病）、贝尔麻痹、雷诺现象", "心肌炎、心肌梗死"], head_fill=GRAY)
    card(s, Emu(6236208), Emu(3200000), Emu(5669280), Emu(1300000), "新版新增 3 项（免疫相关）",
         ["甲状腺功能减退", "痛性眼肌麻痹（Tolosa-Hunt 综合征）", "风湿性多肌痛"], head_fill=RED)
    source_note(s, "依据：CDE 沟通会纪要——完善征集性 AE 与 AESI 监测条目，参照境外已上市同类产品及 CpG 佐剂疫苗相关信息，补充免疫性疾病相关监测内容；安全性与免疫持久性随访至全程免疫后 12 个月；样本量兼顾安全性观察需求。")

    # --- P15 周期与分析策略 ---
    s = content_slide(prs, "调整 ⑨：试验周期缩短与分析策略重写",
                      "随访至全程免疫后 12 个月即可申报；不开展期中分析", 15)
    data = [["项目", "旧版 V1.0", "新版（2026-09-22）"],
            ["试验整体持续时间（首例入组至末例完成末次访视）", "约 26 个月", "约 20 个月"],
            ["受试者个体参与时长（最长程序，0,1,6 月）", "约 24 个月", "约 18 个月"],
            ["分析安排", "首次分析（全程接种后 6 个月安全性随访与相应免疫原性数据锁定后）＋ 末次分析（第 24 个月数据锁定后）", "删除两次分析安排；完成全程免疫后 12 个月随访与数据锁定后申报"]]
    add_table(s, M_LEFT, Emu(1097280), CONTENT_W, Emu(1700000), data,
              col_widths=[28, 36, 36], font_size=9.5)
    card(s, M_LEFT, Emu(3000000), Emu(5669280), Emu(1300000), "依据（CDE 沟通会纪要）",
         ["需完成全程免疫后 12 个月的免疫持久性随访与安全性随访，获得相应数据后方可申报",
          "不建议开展期中分析：不针对免疫原性替代指标开展期中分析并提前揭盲"], head_fill=RED)
    card(s, Emu(6236208), Emu(3000000), Emu(5669280), Emu(1300000), "须同步处理",
         ["正文统计分析章节须明确“仅一次最终分析”，避免摘要与正文不一致",
          "知情同意书、SoA、受试者补偿同步更新；长期持久性依赖Ⅱ期长期随访补充"])
    source_note(s, "注：新版为方案摘要痕迹版，分析策略段为整段删除；正文相应章节需核查后同步修订。")

    prs.save(OUT)
    print("saved ->", OUT, "slides:", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    build()
