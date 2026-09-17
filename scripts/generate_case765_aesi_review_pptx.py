"""
生成《研究号765 AESI/SAE 梳理汇报》PPT。

版式与配色复刻参照文件：
  review_materials/汇报准备输出/TVAX-009_三例死亡SAE梳理汇报.pptx
素材来源：
  review_materials/汇报准备输出/15-肥城现场SAE-远大重组乙肝疫苗二期-研究号765-急性心肌梗死 心衰/
    - 01-...AESI...总结报告-20250903（以此为准）.pdf
    - 20-...心力衰竭-首次报告&总结报告-20250902.pdf
"""

import io
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FONT = "Microsoft YaHei"

C_MAIN = "C00000"  # 主红
C_ACC = "A11C1D"  # 深红强调
C_TEXT = "101010"  # 正文
C_SUB = "595F6B"  # 次文字
C_FOOT = "7A808A"  # 页脚
C_BLUE = "2E75B6"  # 接种节点
C_ORANGE = "C59E5A"  # 症状节点日期
C_GREY = "999999"  # 常规节点
F_BLUE = "CAEDFB"  # 接种节点填充
F_ORANGE = "FAE2D5"  # 症状节点填充
F_RED = "F8D7D7"  # 事件节点填充
F_GREY = "EEEEEE"  # 常规节点填充
F_GREEN = "BBEAD5"  # 表头列 / 结论框
F_ALT = "F5F5F5"  # 隔行底色
F_PANEL = "FBF4F4"  # 封面框 / 章节页面板
L_SPLIT = "BFBFBF"  # 标题下分隔线
L_AXIS = "C9C9C9"  # 时间轴主轴
L_CELL = "D9D9D9"  # 表格细边框

OUT = (
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\汇报准备输出"
    r"\TVAX-009_研究号765_AESI与SAE梳理汇报.pptx"
)


# ---------------------------------------------------------------------------- helpers
def rgb(hex_str):
    return RGBColor.from_string(hex_str)


def set_font(run, size, bold=False, color=C_TEXT, name=FONT):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = rgb(color)
    f.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", name)


def textbox(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    return tb, tf


def put(tf, items, align=PP_ALIGN.LEFT, line_spacing=1.15, anchor=MSO_ANCHOR.TOP):
    """items: list of dict(text,size,bold,color,align,space_after,line_spacing)"""
    tf.vertical_anchor = anchor
    first = True
    for it in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = it.get("align", align)
        p.line_spacing = it.get("line_spacing", line_spacing)
        p.space_after = Pt(it.get("space_after", 0))
        run = p.add_run()
        run.text = it["text"]
        set_font(run, it.get("size", 11), it.get("bold", False), it.get("color", C_TEXT))
    return tf


def rect(slide, l, t, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill:
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = rgb(line)
        sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if sh.has_text_frame:
        sh.text_frame.word_wrap = True
        sh.text_frame.margin_left = sh.text_frame.margin_right = Inches(0.04)
        sh.text_frame.margin_top = sh.text_frame.margin_bottom = Inches(0.02)
    return sh


def set_cell(cell, text, size=9.5, bold=False, color=C_TEXT, bg=None, align=PP_ALIGN.LEFT):
    cell.fill.solid()
    cell.fill.fore_color.rgb = rgb(bg if bg else "FFFFFF")
    tf = cell.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = 1.0
    run = p.add_run()
    run.text = text
    set_font(run, size, bold, color)
    # 细边框
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = tcPr.find(qn(tag))
        if ln is None:
            ln = tcPr.makeelement(qn(tag), {})
            tcPr.append(ln)
        ln.set("w", "6350")
        ln.set("cap", "flat")
        ln.set("cmpd", "sng")
        ln.set("algn", "ctr")
        solid = ln.find(qn("a:solidFill"))
        if solid is None:
            solid = ln.makeelement(qn("a:solidFill"), {})
            ln.append(solid)
        clr = solid.find(qn("a:srgbClr"))
        if clr is None:
            clr = solid.makeelement(qn("a:srgbClr"), {})
            solid.append(clr)
        clr.set("val", L_CELL)


def add_table(
    slide,
    l,
    t,
    w,
    data,
    col_widths,
    row_heights,
    header="red",
    first_col="green",
    body_size=9.5,
    head_size=10.5,
    first_col_size=None,
    first_col_bold=True,
):
    rows, cols = len(data), len(data[0])
    shp = slide.shapes.add_table(
        rows, cols, Inches(l), Inches(t), Inches(w), Inches(sum(row_heights))
    )
    tbl = shp.table
    tbl.first_row = False
    tbl.horz_banding = False
    for i, cw in enumerate(col_widths):
        tbl.columns[i].width = Inches(cw)
    for i, rh in enumerate(row_heights):
        tbl.rows[i].height = Inches(rh)

    head_bg = C_MAIN if header == "red" else "CAEDFB"
    head_fg = "FFFFFF" if header == "red" else C_TEXT
    for r in range(rows):
        alt = r % 2 == 0  # 数据行隔行
        base_bg = "FFFFFF" if alt else F_ALT
        for c in range(cols):
            cell = tbl.cell(r, c)
            txt = data[r][c]
            if r == 0:
                set_cell(
                    cell,
                    txt,
                    size=head_size,
                    bold=True,
                    color=head_fg,
                    bg=head_bg,
                    align=PP_ALIGN.CENTER,
                )
            else:
                if c == 0:
                    bg = F_GREEN if first_col == "green" else base_bg
                    set_cell(
                        cell,
                        txt,
                        size=first_col_size or body_size,
                        bold=first_col_bold,
                        color=C_TEXT,
                        bg=bg,
                    )
                else:
                    set_cell(cell, txt, size=body_size, bold=False, color=C_TEXT, bg=base_bg)
    return shp


def page_no(slide, n):
    tb, tf = textbox(slide, 12.35, 7.05, 0.60, 0.30)
    put(tf, [{"text": str(n), "size": 9, "color": C_FOOT, "align": PP_ALIGN.RIGHT}])


def head_bar(slide, title, subtitle):
    rect(slide, 0.45, 0.16, 0.10, 0.48, fill=C_MAIN)
    tb, tf = textbox(slide, 0.74, 0.20, 11.20, 0.40)
    put(tf, [{"text": title, "size": 14, "bold": True, "color": C_TEXT}])
    tb, tf = textbox(slide, 0.74, 0.94, 11.90, 0.42)
    put(tf, [{"text": subtitle, "size": 12, "bold": True, "color": C_MAIN}])
    rect(slide, 0.45, 0.80, 12.45, 0.02, fill=L_SPLIT)


def note(slide, text, t=6.60, size=8.5, color=C_FOOT, l=0.62, w=12.10, bold=False):
    tb, tf = textbox(slide, l, t, w, 0.40)
    put(tf, [{"text": text, "size": size, "color": color, "bold": bold, "line_spacing": 1.1}])


# ---------------------------------------------------------------------------- page builders
def slide_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0.00, 0.00, 13.33, 0.14, fill=C_MAIN)
    rect(s, 0.00, 7.36, 13.33, 0.14, fill=C_MAIN)
    rect(s, 0.63, 1.55, 12.05, 3.05, fill=F_PANEL, line=C_MAIN, lw=1.2)

    tb, tf = textbox(s, 1.10, 2.00, 11.10, 1.00)
    put(
        tf,
        [
            {
                "text": "研究号765 严重不良事件（AESI／SAE）梳理汇报",
                "size": 30,
                "bold": True,
                "color": C_TEXT,
                "align": PP_ALIGN.CENTER,
            }
        ],
    )
    tb, tf = textbox(s, 1.10, 3.05, 11.10, 0.50)
    put(
        tf,
        [
            {
                "text": "急性非ST段抬高型心肌梗死 · 心力衰竭",
                "size": 15,
                "bold": False,
                "color": C_MAIN,
                "align": PP_ALIGN.CENTER,
            }
        ],
    )
    tb, tf = textbox(s, 1.10, 3.62, 11.10, 0.45)
    put(
        tf,
        [
            {
                "text": "重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅱ期临床试验",
                "size": 11,
                "color": C_SUB,
                "align": PP_ALIGN.CENTER,
            }
        ],
    )

    tb, tf = textbox(s, 1.10, 5.15, 11.10, 0.95)
    put(
        tf,
        [
            {"text": "远大赛威信生命科学（南京）有限公司", "size": 13, "align": PP_ALIGN.CENTER},
            {
                "text": "研究负责单位：山东省疾病预防控制中心｜报告单位：肥城市疾病预防控制中心",
                "size": 10.5,
                "color": C_SUB,
                "align": PP_ALIGN.CENTER,
                "space_after": 2,
            },
            {
                "text": "方案编号：YDSWX（TVAX-009）-002（Ⅱ）｜批准文号：2023LP00500｜2026年09月",
                "size": 10.5,
                "color": C_SUB,
                "align": PP_ALIGN.CENTER,
            },
        ],
    )
    return s


def slide_toc(prs, num):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0.45, 0.16, 0.10, 0.48, fill=C_MAIN)
    tb, tf = textbox(s, 0.74, 0.20, 11.20, 0.40)
    put(tf, [{"text": "汇报内容", "size": 14, "bold": True}])
    rect(s, 0.45, 0.80, 12.45, 0.02, fill=L_SPLIT)

    items = [
        ("01", "事件总览与判定依据", "AESI与SAE双报对照｜相关性判定方法"),
        ("02", "受试者画像与接种史", "人口学｜接种记录｜既往史与个人史"),
        ("03", "完整时间轴", "接种→胸痛→急性心梗→PCI→转归"),
        ("04", "诊疗经过与关键证据", "住院诊疗｜冠脉造影｜心肌标志物演变"),
        ("05", "相关性判定与结论", "五维度评估｜判定结论"),
        ("06", "管理提示与后续建议", "数据修订｜问诊质量｜随访提示"),
    ]
    top = 1.50
    for i, (num_txt, title, sub) in enumerate(items):
        rect(s, 1.83, top, 0.92, 0.72, fill=C_MAIN)
        tb, tf = textbox(s, 1.83, top + 0.14, 0.92, 0.45)
        put(
            tf,
            [
                {
                    "text": num_txt,
                    "size": 22,
                    "bold": True,
                    "color": "FFFFFF",
                    "align": PP_ALIGN.CENTER,
                }
            ],
        )
        tb, tf = textbox(s, 3.05, top + 0.03, 8.60, 0.38)
        put(tf, [{"text": title, "size": 15, "bold": True}])
        tb, tf = textbox(s, 3.05, top + 0.42, 8.60, 0.30)
        put(tf, [{"text": sub, "size": 10, "color": C_SUB}])
        if i < len(items) - 1:
            rect(s, 3.05, top + 0.78, 9.00, 0.01, fill="E0E0E0")
        top += 0.86
    page_no(s, num)
    return s


def slide_section(prs, num, seq, title, bullets, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0.00, 0.00, 0.14, 7.50, fill=C_MAIN)
    rect(s, 8.60, 0.00, 4.73, 7.50, fill=F_PANEL)
    rect(s, 8.60, 0.00, 0.04, 7.50, fill=C_MAIN)
    tb, tf = textbox(s, 0.85, 1.45, 5.00, 1.85)
    put(tf, [{"text": seq, "size": 54, "bold": True, "color": C_MAIN}])
    tb, tf = textbox(s, 0.90, 3.45, 7.20, 0.90)
    put(tf, [{"text": title, "size": 24, "bold": True, "line_spacing": 1.05}])
    rect(s, 0.95, 4.55, 3.20, 0.05, fill=C_MAIN)

    tb, tf = textbox(s, 8.95, 1.55, 4.00, 2.60)
    put(
        tf,
        [{"text": "本章核心", "size": 12, "bold": True, "color": C_MAIN, "space_after": 6}]
        + [{"text": "· " + b, "size": 11, "space_after": 5, "line_spacing": 1.1} for b in bullets],
    )

    tb, tf = textbox(s, 0.85, 6.70, 7.00, 0.30)
    put(
        tf,
        [{"text": "TVAX-009 Ⅱ期临床试验｜研究号765 AESI／SAE梳理汇报", "size": 9, "color": C_FOOT}],
    )
    page_no(s, page)
    return s


def slide_overview(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s,
        "研究号765 事件总览",
        "同一住院事件双报：AESI（急性非ST段抬高型心肌梗死）＋SAE（心力衰竭），均判“可能无关”",
    )

    data = [
        ["项目", "AESI 报告（以此为准）", "SAE 报告"],
        ["事件名称（医学术语）", "冠状动脉粥样硬化性心脏病\n急性非ST段抬高型心肌梗死", "心力衰竭"],
        [
            "报告类型 / 报告日期",
            "AESI 总结报告\n2025-09-03（以此为准）",
            "SAE 首次报告＋总结报告\n2025-09-02",
        ],
        [
            "报告表卡编号",
            "SDCDC-XC-SOP-CX-YDYG-025(F)-001-01",
            "SDCDC-XC-SOP-CX-YDYG-019(F)-002-01",
        ],
        ["严重程度 / SAE 标准", "3 级", "3 级（导致住院）"],
        ["事件开始时间", "2025-04-UK（经病历核实修订）", "2025-06-18"],
        ["事件结束时间", "2025-07-15（AE 结束时间）", "2025-06-28（AE 结束 2025-07-15）"],
        [
            "研究者获知时间",
            "2025-06-19 17:07（第8个月采血现场获知）",
            "2025-08-28 10:45（递交住院病历复印件时获知）",
        ],
        ["事件转归", "痊愈 / 恢复", "痊愈 / 恢复"],
        ["对试验疫苗采取的措施", "不适用（已完成全程接种）", "不适用（已完成全程接种）"],
        ["相关性判定", "可能无关", "可能无关"],
        ["报告单位", "肥城市疾病预防控制中心", "肥城市疾病预防控制中心"],
    ]
    add_table(
        s,
        0.62,
        1.52,
        12.10,
        data,
        col_widths=[2.55, 4.85, 4.70],
        row_heights=[0.34] + [0.40] * 11,
        header="red",
        first_col="green",
        body_size=9.5,
        head_size=10.5,
    )
    note(
        s,
        "注：AESI 开始时间经病历核实由 2025-06-18 修订为 2025-04-UK（第3剂接种前已出现胸痛症状）；"
        "高脂血症作合并疾病上报，不单独计为 SAE。报告日期为总结报告定稿日期。",
        t=6.62,
    )
    page_no(s, page)
    return s


def slide_method(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s,
        "相关性判定依据与方法",
        "《药物临床试验不良事件相关性评价技术指导原则（试行）》＋项目参考原则（V5）",
    )

    tb, tf = textbox(s, 0.74, 1.38, 12.00, 0.32)
    put(tf, [{"text": "综合评估的五个方面：", "size": 12, "bold": True, "color": C_ACC}])
    data = [
        ["评估维度", "本例（研究号765）中的对应考量"],
        [
            "① 合理的时间关系",
            "急性心梗距第3剂接种 59 天（近2个月）；且病历核实提示胸痛症状起始于第3剂接种前（2025-04-UK）——时序性不支持疫苗诱发",
        ],
        [
            "② 药物作用机制／已知不良反应",
            "重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）为预防用生物制品，无致急性心肌梗死或心力衰竭的机制依据；未见同类 CpG 佐剂疫苗相关信号",
        ],
        [
            "③ 去激发结果",
            "事件发生后受试者未再接种（未再暴露），经规范治疗后痊愈，不支持疫苗持续驱动",
        ],
        ["④ 再激发结果", "不适用（全程接种已完成，且再激发不符合伦理）"],
        [
            "⑤ 其他合理解释",
            "冠脉造影直接证实 LAD 完全闭塞、主动脉及冠状动脉硬化；合并高脂血症、吸烟饮酒史、68岁男性——动脉粥样硬化性心血管病危险因素完整",
        ],
    ]
    add_table(
        s,
        0.74,
        1.76,
        11.90,
        data,
        col_widths=[2.90, 9.00],
        row_heights=[0.36, 0.52, 0.62, 0.46, 0.40, 0.58],
        header="blue",
        first_col="plain",
        body_size=10.0,
        head_size=10.5,
    )

    tb, tf = textbox(s, 0.74, 4.55, 12.00, 0.32)
    put(
        tf,
        [
            {
                "text": "项目《不良事件相关性判定参考原则》（V5）关键规则：",
                "size": 12,
                "bold": True,
                "color": C_ACC,
            }
        ],
    )
    tb, tf = textbox(s, 0.74, 4.95, 12.00, 1.60)
    put(
        tf,
        [
            {
                "text": "· 五级判定：肯定有关 / 很可能有关 / 可能有关 / 可能无关 / 无关",
                "size": 10.5,
                "space_after": 5,
            },
            {
                "text": "· 接种 30 天后发生的非征集性事件：有明确诱因或病原学诊断 → 判“无关”；不能明确排除但存在诱因 → 判“可能无关”",
                "size": 10.5,
                "space_after": 5,
            },
            {
                "text": "· 本例事件发生于全程接种后约 2 个月，且存在明确冠脉病变基础与心血管危险因素，报告最终判定为“可能无关”",
                "size": 10.5,
                "space_after": 5,
            },
            {
                "text": "· 现场无法判定时召开会议、聘请相关领域专家进行最终判定（本项目既往三例死亡SAE均经专题会议论证）",
                "size": 10.5,
            },
        ],
    )
    page_no(s, page)
    return s


def slide_profile(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s, "受试者画像与接种史", "研究号765（拼音缩写 ZWQ），男，1956-07-10 出生，169cm / 66.7kg"
    )

    data = [
        ["项目", "内容"],
        ["人口学", "男，1956-07-10 出生（事件发生时 68 岁）；身高 169 cm，体重 66.7 kg"],
        ["分组与程序", "0,1,6 月程序组｜全程接种 3 剂，已完成"],
        [
            "接种记录",
            "第1剂 2024-10-21 15:57；第2剂 2024-11-20 09:15；第3剂 2025-04-20 09:21；"
            "三剂接种后 30 分钟内均无不良事件发生",
        ],
        [
            "入组时自述",
            "疾病史或过敏史：无；合并用药：有（详见用药清单）；自述平时生活规律、身体健康",
        ],
        ["个人史", "适量饮酒、抽烟（受试者口述），无其他不良嗜好"],
        [
            "病历核实（关键）",
            "第3剂接种前（2025-04-UK）已因“活动后左胸部针刺样疼痛，休息 2–3 分钟缓解”"
            "至新城镇社区卫生服务中心就诊，心电图未见明显异常，门诊诊断“胸痛”，"
            "予琥珀酸美托洛尔缓释片 23.75 mg qd、复方丹参滴丸 3 片 tid",
        ],
        [
            "接种第3剂时问诊",
            "受试者因胸痛症状轻微，2025-04-20 接种第3剂问诊时未告知研究者有胸痛症状及正在服用药物",
        ],
        [
            "危险因素谱",
            "68 岁男性、吸烟饮酒史、高脂血症（TC 5.88 mmol/L、LDL-C 4.17 mmol/L）、"
            "冠脉／主动脉硬化（CT 与造影证实）",
        ],
    ]
    add_table(
        s,
        0.62,
        1.50,
        12.10,
        data,
        col_widths=[2.30, 9.80],
        row_heights=[0.34, 0.38, 0.36, 0.50, 0.44, 0.34, 0.78, 0.50, 0.52],
        header="red",
        first_col="green",
        body_size=9.5,
        head_size=10.5,
    )
    tb, tf = textbox(s, 0.62, 6.05, 12.10, 0.52)
    put(
        tf,
        [
            {
                "text": "要点：本例最重要的背景信息——受试者在接种第3剂之前已出现胸痛症状并在服用心血管药物，"
                "但接种问诊时未告知。这既是判定“可能无关”的关键事实基础，也提示接种前问诊需强化"
                "“近期症状＋在用药物”的逐项核查。",
                "size": 10,
                "bold": True,
                "color": C_ACC,
                "line_spacing": 1.12,
            },
        ],
    )
    page_no(s, page)
    return s


def slide_timeline(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s,
        "完整时间轴",
        "首剂接种至痊愈：约 9 个月；急性心梗距第3剂接种 59 天，症状起始早于第3剂接种",
    )

    tb, tf = textbox(s, 0.62, 1.52, 12.10, 0.90)
    put(
        tf,
        [
            {
                "text": "疾病演变主线：冠脉粥样硬化基础 → 活动后胸痛（第3剂接种前已出现）→ 急性非ST段抬高型心肌梗死"
                " → 心力衰竭 → PCI 治疗后好转出院",
                "size": 11,
                "bold": True,
                "color": C_ACC,
                "space_after": 4,
                "line_spacing": 1.1,
            },
            {
                "text": "时间关联性：AESI 症状起始于 2025-04-UK（第3剂接种前）；急性心肌梗死发生于 2025-06-18，"
                "距第3剂接种 2025-04-20 共 59 天（近 2 个月）",
                "size": 11,
                "bold": True,
                "color": C_ACC,
                "line_spacing": 1.1,
            },
        ],
    )

    nodes = [
        ("2024-10-21", "第1剂\n试验用疫苗", "vaccine"),
        ("2024-11-20", "第2剂\n试验用疫苗", "vaccine"),
        ("2025-04-UK", "活动后胸痛\n社区就诊\n（第3剂前）", "symptom"),
        ("2025-04-20", "第3剂\n试验用疫苗", "vaccine"),
        ("2025-06-18", "急性心梗\n收入院", "event"),
        ("2025-06-20", "冠脉造影\nLAD球囊", "event"),
        ("2025-06-28", "好转出院", "event"),
        ("2025-07-15", "复查\n未见异常", "normal"),
    ]
    style = {
        "vaccine": (F_BLUE, C_BLUE, C_BLUE),
        "symptom": (F_ORANGE, C_ACC, C_ORANGE),
        "event": (F_RED, C_MAIN, C_ACC),
        "normal": (F_GREY, C_GREY, C_GREY),
    }
    x = 0.62
    nw, gap = 1.44, 0.08
    node_top, node_h = 2.44, 1.24
    for date, label, kind in nodes:
        fill, line, dcolor = style[kind]
        rect(s, x, node_top, nw, node_h, fill=fill, line=line, lw=0.75)
        sh = s.shapes[-1]
        tf = sh.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        put(
            tf,
            [{"text": label, "size": 8.5, "align": PP_ALIGN.CENTER, "line_spacing": 1.05}],
            anchor=MSO_ANCHOR.MIDDLE,
        )
        tb, tf = textbox(s, x, node_top - 0.28, nw, 0.26)
        put(
            tf, [{"text": date, "size": 9, "bold": True, "color": dcolor, "align": PP_ALIGN.CENTER}]
        )
        x += nw + gap
    rect(s, 0.62, node_top + 0.60, 12.10, 0.03, fill=L_AXIS)

    tb, tf = textbox(s, 0.62, 3.98, 12.10, 0.32)
    put(tf, [{"text": "关键节点明细：", "size": 12, "bold": True, "color": C_ACC}])
    data = [
        ["日期", "节点", "关键信息"],
        [
            "2025-04-UK",
            "第3剂接种前",
            "活动后左胸部针刺样疼痛，休息 2–3 分钟缓解；社区中心就诊，心电图未见明显异常，"
            "诊断“胸痛”；予美托洛尔缓释片 23.75 mg qd＋复方丹参滴丸 3 片 tid",
        ],
        [
            "2025-06-18",
            "发病入院",
            "凌晨 1 点睡梦中突发左胸部疼痛，伴胸闷出汗，约 10 分钟胸痛缓解、胸闷持续不缓解；"
            "门诊心电图：窦性心律、显著 ST 压低（可能示心内膜下心肌损伤）、T 波异常（可能是前侧壁心肌缺血）、"
            "R 波递增不良；以“急性冠脉综合征”收住院；BP 137/100 mmHg",
        ],
        [
            "2025-06-20",
            "冠脉造影＋PCI",
            "冠脉右优势型；LM 内膜光滑无狭窄，LAD 完全闭塞，LCX 细小、内膜光滑无狭窄，"
            "RCA 中段狭窄约 30%、远段供应 LAD 远段；于 LAD 植入药物球囊",
        ],
        [
            "2025-06-28",
            "出院",
            "病情好转出院；出院诊断：冠状动脉粥样硬化性心脏病 急性非ST段抬高型心肌梗死／心力衰竭／高脂血症；"
            "院外规律服药，监测心率血压",
        ],
        [
            "2025-07-15",
            "返院复查",
            "HDL-C 1.01 mmol/L、LDL-C 2.62 mmol/L；血常规、肝功能、电解质、心电图均未见异常；未复查心脏彩超",
        ],
    ]
    add_table(
        s,
        0.62,
        4.34,
        12.10,
        data,
        col_widths=[1.25, 1.55, 9.30],
        row_heights=[0.32, 0.44, 0.54, 0.46, 0.42, 0.36],
        header="blue",
        first_col="plain",
        body_size=9.0,
        head_size=10.0,
    )
    page_no(s, page)
    return s


def slide_treatment(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(s, "住院诊疗经过", "肥城市人民医院；住院 10 天（2025-06-18 ~ 2025-06-28），好转出院")

    data = [
        ["项目", "内容"],
        [
            "入院主诉",
            "“阵发性胸痛 2 月，加重半天”；2 月前开始出现活动后左胸部针刺样疼痛，休息 2–3 分钟缓解，"
            "平日应用“美托洛尔缓释片 23.75 mg qd、丹参”，效果欠佳，未再行特殊治疗",
        ],
        [
            "体格检查",
            "T 36 ℃、P 63 次/分、R 16 次/分、BP 137/100 mmHg；一般状况可，心肺听诊未见明显异常",
        ],
        ["入院诊断", "冠状动脉粥样硬化性心脏病 不稳定型心绞痛"],
        [
            "心电图（06-18）",
            "窦性心律，显著 ST 压低（可能示心内膜下心肌损伤），T 波异常（可能是前侧壁心肌缺血），"
            "R 波递增不良，左心室高电压",
        ],
        [
            "心脏彩超",
            "LA 30 mm，EF 50%，节段性室壁动度不良，三尖瓣反流（轻–中度），主动脉瓣反流（轻度）",
        ],
        [
            "胸部 CT（06-25）",
            "双肺少许炎性病变、右侧少量胸腔积液；右肺钙化灶；右肺结节灶（建议年度随诊）；"
            "主动脉及冠状动脉硬化",
        ],
        [
            "实验室检查",
            "TC 5.88 mmol/L、LDL-C 4.17 mmol/L；Hb 121 g/L；大便隐血弱阳性；"
            "06-23 肝功能 TP 55.5 g/L、ALB 32.5 g/L；NT-proBNP 448.64 pg/mL；D-二聚体 498.07 ng/mL",
        ],
        [
            "主要治疗",
            "抗血小板（阿司匹林＋氯吡格雷）、抗凝（低分子肝素钙）、脱水利尿、纠正心衰、调脂稳定斑块、"
            "改善循环、营养心肌；LAD 药物球囊植入术",
        ],
        [
            "治疗与转归",
            "经治疗后胸部胀痛、头晕症状消失；2025-06-28 病情好转出院；院外规律服药，"
            "2025-07-15 复查未见异常，目前一般情况好，能正常生活",
        ],
    ]
    add_table(
        s,
        0.62,
        1.50,
        12.10,
        data,
        col_widths=[2.15, 9.95],
        row_heights=[0.32, 0.50, 0.36, 0.34, 0.44, 0.40, 0.44, 0.50, 0.50, 0.44],
        header="red",
        first_col="green",
        body_size=9.0,
        head_size=10.5,
    )
    note(
        s,
        "注：受试者出院后长期用药包括阿司匹林、氯吡格雷、瑞舒伐他汀、美托洛尔缓释片、单硝酸异山梨酯、"
        "螺内酯、达格列净、尼可地尔、麝香保心丸等，详见 SAE 报告用药清单。",
        t=6.62,
    )
    page_no(s, page)
    return s


def slide_markers(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s,
        "关键证据：心肌标志物动态演变",
        "TnI 呈典型“升高—峰值—回落”曲线，符合急性心肌梗死自然病程",
    )

    data = [
        ["采样日期", "TnI（ng/mL）", "CK-MB（ng/mL）", "肌红蛋白（ng/mL）", "其他"],
        ["2025-06-18", "6.95", "57.23", "397.47", "NT-proBNP 448.64 pg/mL；D-二聚体 498.07 ng/mL"],
        ["2025-06-19", "11.84（峰值）", "53.16", "48.51", "—"],
        ["2025-06-24", "0.74", "< 3.00", "18.08", "—"],
        ["2025-06-28", "0.05", "< 3.00", "25.78", "出院日"],
    ]
    add_table(
        s,
        0.62,
        1.55,
        12.10,
        data,
        col_widths=[1.70, 1.95, 1.95, 2.05, 4.45],
        row_heights=[0.36, 0.44, 0.40, 0.40, 0.40],
        header="red",
        first_col="green",
        body_size=10.0,
        head_size=10.5,
    )

    tb, tf = textbox(s, 0.74, 3.78, 11.90, 0.32)
    put(tf, [{"text": "证据解读", "size": 12, "bold": True, "color": C_ACC}])
    y = 4.14
    for title, body in [
        (
            "病因学证据明确",
            "冠脉造影直接证实罪犯血管病变：LAD 完全闭塞，RCA 中段狭窄约 30%，主动脉及冠状动脉硬化——"
            "属典型的动脉粥样硬化性心血管疾病，非免疫介导事件。",
        ),
        (
            "病程演变典型",
            "TnI 由 6.95 → 11.84（峰值）→ 0.74 → 0.05 ng/mL，CK-MB 与肌红蛋白同步回落，"
            "为急性心肌梗死特征性的升高–峰值–回落曲线，与疫苗诱导的急性反应模式不符。",
        ),
        (
            "血栓相关指标不支持疫苗因素",
            "D-二聚体 498.07 ng/mL 轻度升高、NT-proBNP 448.64 pg/mL 升高，"
            "均可用急性冠脉事件与心力衰竭解释；未见疫苗相关血栓性事件的实验室特征。",
        ),
    ]:
        rect(s, 0.74, y + 0.04, 0.07, 0.22, fill=C_MAIN)
        tb, tf = textbox(s, 0.92, y, 11.70, 0.30)
        put(tf, [{"text": title, "size": 11.5, "bold": True, "color": C_ACC}])
        tb, tf = textbox(s, 0.92, y + 0.30, 11.70, 0.48)
        put(tf, [{"text": "· " + body, "size": 11, "line_spacing": 1.12}])
        y += 0.86
    page_no(s, page)
    return s


def slide_judgement(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(
        s, "相关性判定与结论", "依据完整病历、冠脉造影与实验室检查，AESI 与 SAE 均判定“可能无关”"
    )

    data = [
        ["评估维度", "证据与结论"],
        [
            "时间关系",
            "急性心肌梗死距第3剂接种 59 天（近 2 个月）；且病历核实显示胸痛症状起始于第3剂接种前（2025-04-UK）——"
            "时序性不支持疫苗诱发",
        ],
        [
            "机制合理性",
            "重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）为预防用生物制品，用于预防乙型肝炎，"
            "无明确导致急性心肌梗死或心力衰竭的机制依据",
        ],
        [
            "基础疾病权重",
            "冠脉造影证实 LAD 完全闭塞、主动脉及冠状动脉硬化；合并高脂血症（LDL-C 4.17 mmol/L）；"
            "68 岁男性、吸烟饮酒史——危险因素完整",
        ],
        [
            "实验室与器械证据",
            "TnI 典型升高–峰值–回落曲线；心脏彩超 EF 50%、节段性室壁动度不良；冠脉造影明确罪犯病变——"
            "均为动脉粥样硬化性心脏病的表现",
        ],
        [
            "判定结论",
            "AESI（急性非ST段抬高型心肌梗死）与 SAE（心力衰竭）均判定“可能无关”；"
            "两者转归均为痊愈／恢复",
        ],
    ]
    add_table(
        s,
        0.74,
        1.52,
        11.90,
        data,
        col_widths=[2.35, 9.55],
        row_heights=[0.34, 0.52, 0.50, 0.56, 0.52, 0.50],
        header="red",
        first_col="green",
        body_size=10.0,
        head_size=11.0,
    )

    rect(s, 0.74, 4.62, 11.90, 0.98, fill=F_GREEN)
    tb, tf = textbox(s, 0.95, 4.78, 11.48, 0.70)
    put(
        tf,
        [
            {
                "text": "结论：68 岁男性受试者，于全程接种完成后约 2 个月发生急性非ST段抬高型心肌梗死并合并心力衰竭；"
                "症状实际起始于第3剂接种前，冠脉造影证实 LAD 完全闭塞等明确冠脉病变基础，"
                "时间关系不成立、无机制依据、基础疾病与危险因素可完整解释病程，属偶合事件，判定“可能无关”。",
                "size": 11.5,
                "bold": True,
                "line_spacing": 1.16,
            },
        ],
    )

    tb, tf = textbox(s, 0.74, 5.80, 11.90, 0.75)
    put(
        tf,
        [
            {
                "text": "报告原文判定理由：① 心肌梗死的常见病因是冠状动脉粥样硬化、心肌供氧量不足、"
                "心肌耗氧量增加及血栓栓塞；心力衰竭的病因包括原发性／继发性心肌损害、心脏负荷过重、"
                "心室前负荷不足；② 发病距全程接种完疫苗已近 2 个月；③ 试验用疫苗属重组疫苗，"
                "无明确导致心肌梗死的相关依据。",
                "size": 10,
                "color": C_SUB,
                "line_spacing": 1.14,
            },
        ],
    )
    page_no(s, page)
    return s


def slide_conclusion(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    head_bar(s, "结论与管理提示", "基于已收集的完整病历、冠脉造影结果与实验室检查")

    blocks = [
        (
            "判定与结论",
            [
                "· 本例 AESI（急性非ST段抬高型心肌梗死）与 SAE（心力衰竭）均判定“可能无关”，受试者已痊愈，"
                "未触及方案暂停／终止标准",
                "· 与项目既往三例死亡 SAE（774／829／839，均判“无关”）相比，本例判定为“可能无关”，"
                "体现对“距全程接种约 2 个月”这一时间因素的审慎处理",
            ],
        ),
        (
            "数据管理与合规",
            [
                "· 已按“获知 → 首次报告 → 随访报告 → 总结报告”完成闭环；AESI 开始时间经病历核实由 2025-06-18 "
                "修订为 2025-04-UK，修订依据与留痕完整",
                "· 心力衰竭作为出院诊断，研究者于 2025-08-28 递交住院病历复印件时方获知并报告——"
                "提示出院诊断类 SAE 存在获知滞后风险",
                "· 高脂血症作合并疾病上报，避免与 SAE 重复计数",
            ],
        ),
        (
            "对后续研究与现场执行的提示",
            [
                "· 接种前问诊不能仅询问既往史，需逐项核查近期症状与在用药物（本例受试者因症状轻微未告知胸痛及用药）",
                "· 老年及心血管高危人群应加强心血管相关症状的主动问询，并提高随访频次",
                "· 住院事件应尽早调取完整病历（含出院诊断、造影／手术记录、检验单），避免因信息滞后影响报告及时性",
            ],
        ),
    ]
    y = 1.45
    for title, items in blocks:
        rect(s, 0.74, y + 0.06, 0.07, 0.22, fill=C_MAIN)
        tb, tf = textbox(s, 0.92, y, 11.70, 0.30)
        put(tf, [{"text": title, "size": 11.5, "bold": True, "color": C_ACC}])
        tb, tf = textbox(s, 0.92, y + 0.32, 11.70, 0.26 * len(items) + 0.28)
        put(
            tf, [{"text": it, "size": 10.5, "space_after": 4, "line_spacing": 1.12} for it in items]
        )
        y += 0.34 + 0.26 * len(items) + 0.36
    page_no(s, page)
    return s


def slide_thanks(prs, page):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0.00, 0.00, 13.33, 0.14, fill=C_MAIN)
    rect(s, 0.00, 7.36, 13.33, 0.14, fill=C_MAIN)
    tb, tf = textbox(s, 1.00, 2.85, 11.33, 1.00)
    put(tf, [{"text": "谢 谢！", "size": 44, "bold": True, "align": PP_ALIGN.CENTER}])
    tb, tf = textbox(s, 1.00, 4.00, 11.33, 0.50)
    put(
        tf,
        [
            {
                "text": "THANKS FOR YOUR ATTENTION",
                "size": 16,
                "color": C_SUB,
                "align": PP_ALIGN.CENTER,
            }
        ],
    )
    tb, tf = textbox(s, 1.00, 5.00, 11.33, 0.50)
    put(tf, [{"text": "远大赛威信生命科学（南京）有限公司", "size": 12, "align": PP_ALIGN.CENTER}])
    tb, tf = textbox(s, 0.62, 6.95, 12.10, 0.35)
    put(
        tf,
        [
            {
                "text": "数据来源：研究号765 AESI 总结报告（2025-09-03，以此为准）、心力衰竭 SAE 首次＋总结报告"
                "（2025-09-02）；受试者信息已脱敏。",
                "size": 8.5,
                "color": C_FOOT,
                "align": PP_ALIGN.CENTER,
            }
        ],
    )
    page_no(s, page)
    return s


# ---------------------------------------------------------------------------- main
def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide_cover(prs)  # 1
    slide_toc(prs, 2)  # 2
    slide_section(
        prs,
        3,
        "01",
        "事件总览与判定依据",
        [
            "同一住院事件双报：AESI＋SAE",
            "严重程度均为3级，转归均为痊愈",
            "相关性均判定为“可能无关”",
        ],
        3,
    )  # 3
    slide_overview(prs, 4)  # 4
    slide_method(prs, 5)  # 5
    slide_section(
        prs,
        6,
        "02",
        "受试者画像与接种史",
        ["男，68岁，169cm／66.7kg", "0,1,6月程序组，全程接种3剂", "接种第3剂前已有胸痛症状并用药"],
        6,
    )  # 6
    slide_profile(prs, 7)  # 7
    slide_section(
        prs,
        8,
        "03",
        "完整时间轴与疾病演进",
        ["症状起始早于第3剂接种", "急性心梗距第3剂接种59天", "PCI术后10天好转出院"],
        8,
    )  # 8
    slide_timeline(prs, 9)  # 9
    slide_section(
        prs,
        10,
        "04",
        "诊疗经过与关键证据",
        ["冠脉造影证实LAD完全闭塞", "TnI呈典型升高–峰值–回落曲线", "合并高脂血症等多重危险因素"],
        10,
    )  # 10
    slide_treatment(prs, 11)  # 11
    slide_markers(prs, 12)  # 12
    slide_section(
        prs,
        13,
        "05",
        "相关性判定与结论",
        ["五维度综合评估", "时间关系不成立、无机制依据", "基础疾病可完整解释病程"],
        13,
    )  # 13
    slide_judgement(prs, 14)  # 14
    slide_section(
        prs,
        15,
        "06",
        "结论与管理提示",
        ["判定结论与横向对比", "数据修订与获知及时性", "问诊质量与随访提示"],
        15,
    )  # 15
    slide_conclusion(prs, 16)  # 16
    slide_thanks(prs, 17)  # 17

    prs.save(OUT)
    print("SAVED:", OUT)
    print("SLIDES:", len(prs.slides.__iter__.__self__._sldIdLst))


if __name__ == "__main__":
    main()
