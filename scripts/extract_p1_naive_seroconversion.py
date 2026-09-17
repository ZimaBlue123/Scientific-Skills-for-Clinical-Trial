"""
extract_p1_naive_seroconversion.py
================================
P1 一期临床（远大赛威信-重组乙型肝炎疫苗 CpG+铝佐剂）Ⅰ期统计分析报告
—— 从第 1 册 14.2.1.4 / 14.2.1.5 / 14.2.1.6 三个章节的官方汇总表
    直接提取「既往无乙肝疫苗接种史人群」的 GMC 与阳转率数值（不重新计算）。

数据源章节：
  - 14.2.1.4 = 既往无乙肝疫苗接种史人群（全体，FAS=100 例：低 23 + 中 29 + 高 24 + 对 24）
  - 14.2.1.5 = 既往无乙肝疫苗接种史 18-59岁 人群（FAS=77 例：低 18 + 中 23 + 高 18 + 对 18）
  - 14.2.1.6 = 既往无乙肝疫苗接种史 ≥60岁 人群（FAS=23 例：低 5 + 中 6 + 高 6 + 对 6）

子表结构（每个章节完全平行）：
  - .x.1 = 免前抗-HBs
  - .x.2 = 免后抗-HBs（阳转率 + 阳性率 + 4倍增长率 + 阳转(4倍增长)率 + 2 组间比较表）
  - .x.3 = 免后抗-HBs GMC（全体 GMC + 免前阴性人群 GMC + 免前阳性人群 GMC + 较免前增长倍数 + 2 组间比较表）

输出：reports/P1_无接种史_阳转率.xlsx
  Sheet1 = 每组未校正GMC_FAS_无接种史（4 组 × 3 时点，三段堆叠）
  Sheet2 = 每组未校正GMC_PPS_无接种史（4 组 × 3 时点，三段堆叠）
  Sheet3 = FAS_无接种史阳转率（4 组 × 3 时点，三段堆叠）
  Sheet4 = PPS_无接种史阳转率（4 组 × 3 时点，三段堆叠）
  Sheet5 = 口径与方法说明

时点：
  M1 = 首剂免后 1 个月
  M2 = 第 2 剂免后 1 个月
  M6 = 第 3 剂接种前

阳转率口径：采用章节内官方口径（基于"免前阴性人群"子集）
GMC 口径：采用章节内"免前阴性人群 GMC(mIU/mL)"段（R11）
"""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl
from docx import Document
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
DOCX_T1 = (
    BASE
    / "review_materials"
    / "P1 无接种史"
    / "远大赛威信-重组乙型肝炎疫苗（CpG和铝佐剂）Ⅰ期统计分析报告-第1册（人口学+免疫原性评价）.docx"
)
OUT_XLSX = BASE / "reports" / "P1_无接种史_阳转率.xlsx"

GROUPS = ["低剂量组", "中剂量组", "高剂量组", "对照组"]

# 时点 → (中文标签, FAS 表号偏移, PPS 分析集)
TIMEPOINTS = ["M1", "M2", "M6"]
TIMEPOINT_LABELS = {
    "M1": "M1（首剂免后1个月）",
    "M2": "M2（第2剂免后1个月）",
    "M6": "M6（第3剂接种前）",
}
# 各章节阳转率表基础表号（首剂免后1个月, FAS）
SCR_BASE = {
    "14.2.1.4": 147,  # 全体
    "14.2.1.5": 184,  # 18-59岁
    "14.2.1.6": 221,  # ≥60岁
}
# 各章节 GMC 表基础表号（首剂免后1个月, FAS）
GMC_BASE = {
    "14.2.1.4": 157,  # 全体
    "14.2.1.5": 194,  # 18-59岁
    "14.2.1.6": 231,  # ≥60岁
}
# 同章节内不同时点的表号偏移
TP_OFFSET_IN_CHAPTER = {"M1": 0, "M2": 2, "M6": 4}  # 阳转率与 GMC 均为每时点 2 张表（FAS + PPSx）
# 不同时点的 PPS 分析集名称
PPS_SET_BY_TP = {"M1": "PPS1", "M2": "PPS2", "M6": "PPS3"}


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------
def cell_text(cell) -> str:
    return cell.text.strip()


def row_texts(row) -> list[str]:
    return [cell_text(c) for c in row.cells]


def parse_int_from_cell(s: str) -> int:
    """解析「18 (0)」或「n (Missing)」等单元格 → 18。"""
    s = s.strip()
    m = re.match(r"\s*(\d+)\s*\(\s*(\d+)\s*\)", s)
    if m:
        return int(m.group(1))
    m = re.match(r"\s*(\d+)", s)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot parse int from: {s!r}")


def parse_pct_from_cell(s: str) -> float:
    """解析「38.89」或「13 (30.43)」 → 30.43。"""
    s = s.strip()
    m = re.search(r"\(([\d.]+)\s*%?\)", s)
    if m:
        return float(m.group(1))
    m = re.match(r"\s*([\d.]+)\s*%?", s)
    if m:
        return float(m.group(1))
    raise ValueError(f"Cannot parse pct from: {s!r}")


def parse_count_from_pct_cell(s: str) -> int:
    """解析「13 (30.43)」 → 13。"""
    s = s.strip()
    m = re.match(r"\s*(\d+)\s*\(", s)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot parse count from: {s!r}")


def parse_gmc_from_cell(s: str) -> tuple[float, str]:
    """解析「8.490(3.152, 22.864)」 → (8.490, '(3.152, 22.864)')。
    若为 NA 则返回 (None, 'NA')。
    """
    s = s.strip()
    if s.startswith("NA") or "NA" in s and not re.search(r"\d", s):
        return (None, "NA")
    m = re.match(r"\s*([\d.]+)\s*(?:\(([^)]*)\))?", s)
    if not m:
        return (None, s)
    val = float(m.group(1))
    ci = m.group(2) or ""
    return (val, f"({ci})" if ci else "")


# ---------------------------------------------------------------------------
# 章节表 → 数值
# ---------------------------------------------------------------------------
def read_scr_table(doc: Document, table_idx: int) -> dict:
    """读阳转率表 → {group_idx: (阳性数, 阳转率%, 阳转率95%CI, 分母N)}。

    表结构（T184 / T147 验证）：
      R0 = 列头（组别 + N）
      R1 = 段落标题「首剂免后1个月抗-HBs 阳性率」
      R2 = 阳性 n(%)
      R3 = 95%CI
      R4 = 合计(Missing)
      R5 = 段落标题「首剂免后1个月抗-HBs 阳转率」
      R6 = 阳转 n(%)
      R7 = 95%CI  ← 阳转率的 95%CI
      R8 = 合计(Missing)  ← 阳转率分母
    """
    tbl = doc.tables[table_idx]
    rows = [row_texts(r) for r in tbl.rows]
    out = {}
    for gi in range(4):
        cell_pct = rows[6][1 + gi]  # R6 阳转 n(%)
        cell_ci = rows[7][1 + gi]  # R7 95%CI
        cell_den = rows[8][1 + gi]  # R8 合计(Missing)
        n_sero = parse_count_from_pct_cell(cell_pct)
        scr_pct = parse_pct_from_cell(cell_pct)
        den_n = parse_int_from_cell(cell_den)
        out[gi] = {
            "n_sero": n_sero,
            "scr_pct": scr_pct,
            "ci": cell_ci.strip(),
            "den_n": den_n,
        }
    return out


def read_gmc_table(doc: Document, table_idx: int) -> dict:
    """读 GMC 表 → {group_idx: (GMC, GMC 95%CI, 免前阴性N)}。

    表结构（T194 / T157 验证）：
      R1 = 段落标题「首剂免后1个月抗-HBs GMC(mIU/mL)」
      R2 = n (Missing)  ← 全体 N
      R3 = Mean (SD)
      R4 = Geometric Mean(95%CI)  ← 全体 GMC
      ...
      R8 = 段落标题「免前阴性人群首剂免后1个月抗-HBs GMC(mIU/mL)」
      R9 = n (Missing)  ← 免前阴性 N
      R10 = Mean (SD)
      R11 = Geometric Mean(95%CI)  ← 免前阴性人群 GMC（采用这个）
    """
    tbl = doc.tables[table_idx]
    rows = [row_texts(r) for r in tbl.rows]
    out = {}
    for gi in range(4):
        cell_gmc = rows[11][1 + gi]  # R11 免前阴性人群 GMC
        cell_n = rows[9][1 + gi]  # R9 n(Missing)
        gmc_val, gmc_ci = parse_gmc_from_cell(cell_gmc)
        n_neg = parse_int_from_cell(cell_n)
        out[gi] = {
            "gmc": gmc_val,
            "gmc_ci": gmc_ci,
            "n_neg": n_neg,
        }
    return out


def fetch_table_idx(chapter: str, kind: str, tp: str, analysis: str) -> int:
    """获取某章节某时点某分析集的表号。

    chapter: '14.2.1.4' / '14.2.1.5' / '14.2.1.6'
    kind: 'scr' / 'gmc'
    tp: 'M1' / 'M2' / 'M6'
    analysis: 'FAS' / 'PPS1' / 'PPS2' / 'PPS3'
    """
    base = (SCR_BASE if kind == "scr" else GMC_BASE)[chapter]
    offset = TP_OFFSET_IN_CHAPTER[tp]
    if analysis == "FAS":
        return base + offset
    # PPS 紧跟 FAS 之后
    return base + offset + 1


# ---------------------------------------------------------------------------
# Excel 样式
# ---------------------------------------------------------------------------
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
GROUP_FILLS = {
    "低剂量组": PatternFill("solid", fgColor="DDEBF7"),
    "中剂量组": PatternFill("solid", fgColor="FFF2CC"),
    "高剂量组": PatternFill("solid", fgColor="FCE4D6"),
    "对照组": PatternFill("solid", fgColor="E2EFDA"),
}
TOTAL_FILL = PatternFill("solid", fgColor="D9D9D9")
NOTE_FILL = PatternFill("solid", fgColor="F2F2F2")
SECTION_FILL_18_59 = PatternFill("solid", fgColor="E7E6E6")
SECTION_FILL_60_PLUS = PatternFill("solid", fgColor="FCE4D6")
SECTION_FILL_TOTAL = PatternFill("solid", fgColor="305496")
THIN = Side(border_style="thin", color="B4B4B4")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def section_fill(age_group: str) -> PatternFill:
    if age_group == "总体":
        return SECTION_FILL_TOTAL
    return SECTION_FILL_60_PLUS if age_group == "≥60岁" else SECTION_FILL_18_59


def section_label(age_group: str) -> str:
    if age_group == "总体":
        return "【总体（既往无乙肝疫苗接种史人群全体）】"
    return f"【{age_group} 既往无乙肝疫苗接种史人群】"


# ---------------------------------------------------------------------------
# Sheet1/Sheet2：每组未校正 GMC（取自 14.2.1.5/6/4 三个章节的 GMC 表 R11）
# ---------------------------------------------------------------------------
def write_gmc_sheet(ws, analysis_label: str):
    """写入一张 GMC 汇总表（4 组 × 3 时点，三段堆叠）。

    18-59岁 段 ← 14.2.1.5
    ≥60岁 段 ← 14.2.1.6
    总体段 ← 14.2.1.4
    """
    ws.title = f"每组未校正GMC_{analysis_label}_无接种史"

    headers = ["组别", "N（免前<10）", "M1\n首剂免后1个月", "M2\n第2剂免后1个月", "M6\n第3剂接种前"]
    n_cols = len(headers)
    for j, h in enumerate(headers, 1):
        c = ws.cell(1, j, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

    # 段 → 章节映射
    segment_to_chapter = [("18-59岁", "14.2.1.5"), ("≥60岁", "14.2.1.6"), ("总体", "14.2.1.4")]

    row = 2
    for seg_label, chapter in segment_to_chapter:
        if seg_label != "18-59岁":
            row += 1
        title_cell = ws.cell(row=row, column=1, value=section_label(seg_label))
        if seg_label == "总体":
            title_cell.font = Font(bold=True, size=12, color="FFFFFF")
        else:
            title_cell.font = Font(bold=True, size=12, color="C00000")
        title_cell.fill = section_fill(seg_label)
        title_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        title_cell.border = BORDER
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=n_cols)
        row += 1

        for gi, grp in enumerate(GROUPS):
            # M1 读 n（用 N 值列）
            ti_m1 = fetch_table_idx(chapter, "gmc", "M1", analysis_label)
            m1 = read_gmc_table(DOC, ti_m1)[gi]
            n_neg_display = m1["n_neg"]

            cells = [grp, f"{n_neg_display}"]
            for tp in TIMEPOINTS:
                ti = fetch_table_idx(chapter, "gmc", tp, analysis_label)
                rec = read_gmc_table(DOC, ti)[gi]
                gmc_val = rec["gmc"]
                gmc_ci = rec["gmc_ci"]
                if gmc_val is None:
                    cells.append("NA")
                else:
                    cells.append(f"{gmc_val:.3f} {gmc_ci}".strip())
            for j, v in enumerate(cells, 1):
                c = ws.cell(row=row, column=j, value=v)
                c.fill = GROUP_FILLS.get(grp, PatternFill())
                c.border = BORDER
                c.alignment = CENTER
            row += 1

        # 段合计
        cells = ["合计", "—"]
        for tp in TIMEPOINTS:
            ti = fetch_table_idx(chapter, "gmc", tp, analysis_label)
            all_recs = read_gmc_table(DOC, ti)
            vals = [r["gmc"] for r in all_recs.values() if r["gmc"] is not None]
            [r["n_neg"] for r in all_recs.values()]
            if vals:
                avg = sum(vals) / len(vals)
                cells.append(f"{avg:.3f}")
            else:
                cells.append("NA")
            # 总N 显示
        # 修正：第2列应该是 4 组 N 之和
        ti_m1_for_total = fetch_table_idx(chapter, "gmc", "M1", analysis_label)
        total_n = sum(r["n_neg"] for r in read_gmc_table(DOC, ti_m1_for_total).values())
        cells[1] = f"{total_n}"

        for j, v in enumerate(cells, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.fill = TOTAL_FILL
            c.border = BORDER
            c.alignment = CENTER
            c.font = Font(bold=True)
        row += 1

    # 备注
    row += 1
    note_cell = ws.cell(row=row, column=1, value="GMC 数据源")
    note_cell.font = Font(bold=True, italic=True)
    note_cell.alignment = CENTER
    note_cell.border = BORDER
    note_cell.fill = NOTE_FILL
    note = ws.cell(
        row=row,
        column=2,
        value="第 1 册 14.2.1.4（全体）/ 14.2.1.5（18-59岁）/ 14.2.1.6（≥60岁）三个章节的"
        "「.x.3 免后抗-HBs GMC」汇总表 R11「免前阴性人群 GMC(mIU/mL)」段。",
    )
    note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    note.border = BORDER
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=n_cols)
    row += 1

    note_cell = ws.cell(row=row, column=1, value="合计说明")
    note_cell.font = Font(bold=True, italic=True)
    note_cell.alignment = CENTER
    note_cell.border = BORDER
    note_cell.fill = NOTE_FILL
    note = ws.cell(
        row=row,
        column=2,
        value="合计行的 GMC = 4 组 GMC 算术均值（仅参考）；N（免前<10）= 4 组有效样本量之和。",
    )
    note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    note.border = BORDER
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=n_cols)

    widths = [10, 14, 22, 22, 22]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[1].height = 38
    ws.freeze_panes = "C2"


# ---------------------------------------------------------------------------
# Sheet3/Sheet4：FAS / PPS 阳转率（取自 14.2.1.5/6/4 三个章节的阳转率表 R6/R7/R8）
# ---------------------------------------------------------------------------
def write_scr_sheet(ws, analysis_label: str):
    """写入一张阳转率表（4 组 × 3 时点，三段堆叠）。"""
    ws.title = f"{analysis_label}_无接种史阳转率"

    headers = [
        "组别",
        "分析集",
        "年龄层",
        "M1\n首剂免后1个月\nn/N (%)",
        "M1\n95%CI",
        "M2\n第2剂免后1个月\nn/N (%)",
        "M2\n95%CI",
        "M6\n第3剂接种前\nn/N (%)",
        "M6\n95%CI",
    ]
    n_cols = len(headers)
    for j, h in enumerate(headers, 1):
        c = ws.cell(1, j, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

    # 时点列索引

    segment_to_chapter = [("18-59岁", "14.2.1.5"), ("≥60岁", "14.2.1.6"), ("总体", "14.2.1.4")]

    row = 2
    for seg_label, chapter in segment_to_chapter:
        if seg_label != "18-59岁":
            row += 1
        title_cell = ws.cell(row=row, column=1, value=section_label(seg_label))
        if seg_label == "总体":
            title_cell.font = Font(bold=True, size=12, color="FFFFFF")
        else:
            title_cell.font = Font(bold=True, size=12, color="C00000")
        title_cell.fill = section_fill(seg_label)
        title_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        title_cell.border = BORDER
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=n_cols)
        row += 1

        for gi, grp in enumerate(GROUPS):
            cells = [grp, analysis_label, seg_label]
            for tp in TIMEPOINTS:
                ti = fetch_table_idx(chapter, "scr", tp, analysis_label)
                rec = read_scr_table(DOC, ti)[gi]
                cells.append(f"{rec['n_sero']}/{rec['den_n']} ({rec['scr_pct']:.2f})")
                cells.append(rec["ci"] if rec["ci"] else "—")
            for j, v in enumerate(cells, 1):
                c = ws.cell(row=row, column=j, value=v)
                c.fill = GROUP_FILLS.get(grp, PatternFill())
                c.border = BORDER
                c.alignment = CENTER
            row += 1

        # 段合计：分子分母分别相加，阳转率 = 总分子/总分母
        cells = ["合计", analysis_label, seg_label]
        for tp in TIMEPOINTS:
            ti = fetch_table_idx(chapter, "scr", tp, analysis_label)
            all_recs = read_scr_table(DOC, ti)
            total_n_sero = sum(r["n_sero"] for r in all_recs.values())
            total_den = sum(r["den_n"] for r in all_recs.values())
            scr_pct = total_n_sero / total_den * 100 if total_den > 0 else float("nan")
            cells.append(f"{total_n_sero}/{total_den} ({scr_pct:.2f})")
            cells.append("—")  # CI 不加权合计
        for j, v in enumerate(cells, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.fill = TOTAL_FILL
            c.border = BORDER
            c.alignment = CENTER
            c.font = Font(bold=True)
        row += 1

    # 备注
    row += 1
    note_cell = ws.cell(row=row, column=1, value="数据源")
    note_cell.font = Font(bold=True, italic=True)
    note_cell.alignment = CENTER
    note_cell.border = BORDER
    note_cell.fill = NOTE_FILL
    note = ws.cell(
        row=row,
        column=2,
        value="第 1 册 14.2.1.4（全体）/ 14.2.1.5（18-59岁）/ 14.2.1.6（≥60岁）三个章节的"
        "「.x.2 免后抗-HBs」汇总表的「阳转率」段（R6 阳转 n(%) + R8 合计）。"
        "95%CI 为 Clopper-Pearson 法（章节内官方值）。",
    )
    note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    note.border = BORDER
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=n_cols)

    widths = [10, 8, 9, 18, 16, 18, 16, 18, 16]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[1].height = 50
    ws.freeze_panes = "D2"


# ---------------------------------------------------------------------------
# Sheet5：口径与方法说明
# ---------------------------------------------------------------------------
def write_methodology_sheet(ws):
    ws.title = "口径与方法说明"
    lines = [
        ["项目", "P1 一期临床试验（远大赛威信-重组乙型肝炎疫苗，CpG+铝佐剂）"],
        ["数据源", "review_materials/P1 无接种史/第 1 册（人口学+免疫原性评价）.docx"],
        [
            "",
            "14.2.1.4 既往无乙肝疫苗接种史人群体液免疫评价（全体）"
            "14.2.1.5 既往无乙肝疫苗接种史 18-59岁 人群体液免疫评价"
            "14.2.1.6 既往无乙肝疫苗接种史 ≥60岁 人群体液免疫评价",
        ],
        [
            "人群样本量（FAS）",
            "14.2.1.4 全体：低剂量 23 + 中剂量 29 + 高剂量 24 + 对照 24 = 100 例"
            "14.2.1.5 18-59岁：低 18 + 中 23 + 高 18 + 对 18 = 77 例"
            "14.2.1.6 ≥60岁：低 5 + 中 6 + 高 6 + 对 6 = 23 例",
        ],
        [
            "既往无乙肝疫苗接种史人群定义",
            "依据方案入排标准：受试者既往未接种过乙肝疫苗（章节标题口径）。本章节评价对象即此子集。",
        ],
        ["", ""],
        [
            "阳转率（SCR）定义",
            "免前抗-HBs < 10 mIU/mL 的受试者（章节「免前阴性人群」子集）中，免后抗-HBs ≥ 10 mIU/mL 者的百分比",
        ],
        ["SCR 分子 / 分母", "分子 = 阳转人数（章节 R6 字段）；分母 = 该时点合计 N（章节 R8 字段）"],
        ["SCR 95% CI", "Clopper-Pearson 法（章节内官方 CI，直接采用）"],
        ["", ""],
        [
            "GMC 定义",
            "免前阴性人群首剂 / 第 2 剂 / 第 3 剂接种前 的抗-HBs 几何均值浓度（章节 R11 段）",
        ],
        ["GMC 计算", "GMC = exp(mean(log(anti-HBs mIU/mL)))—— 章节内官方计算结果，直接采用"],
        ["GMC 95% CI", "经对数变换后估计（章节内官方 CI，直接采用）"],
        ["", ""],
        ["时间点定义", "M1 = 首剂免后 1 个月 = 首剂后 1 个月采血"],
        ["", "M2 = 第 2 剂免后 1 个月 = 首剂后 2 个月采血"],
        ["", "M6 = 第 3 剂接种前 = 首剂后 6 个月采血（即 0-1-6 月程序的第 3 剂接种前时点）"],
        ["", ""],
        [
            "分析集说明",
            "FAS = 全分析集（含所有随机入组的受试者；不剔除方案偏离/违背）"
            "PPS = 符合方案集（剔除方案偏离/违背）；PPS1=M1时点，PPS2=M2时点，PPS3=M6前时点",
        ],
        ["", ""],
        [
            "GMC 汇总来源（Sheet1/Sheet2）",
            "Sheet1（FAS）= 第 1 册 GMC 汇总表 R11（免前阴性人群 GMC）："
            "18-59岁=T194/T196/T198，≥60岁=T231/T233/T235，全体=T157/T159/T161；"
            "Sheet2（PPS）= T195/T197/T199 + T232/T234/T236 + T158/T160/T162",
        ],
        [
            "阳转率来源（Sheet3/Sheet4）",
            "Sheet3（FAS）= 第 1 册 阳转率表 R6/R8："
            "18-59岁=T184/T186/T188，≥60岁=T221/T223/T225，全体=T147/T149/T151；"
            "Sheet4（PPS）= T185/T187/T189 + T222/T224/T226 + T148/T150/T152",
        ],
        ["", ""],
        [
            "组别",
            "低剂量组 / 中剂量组 / 高剂量组 / 对照组（汉逊酵母重组乙型肝炎疫苗，CpG ODN + 铝佐剂）",
        ],
        ["", ""],
        [
            "重要提示",
            "≥60岁 子集样本量较小（N=6/组），统计推断需谨慎。"
            "建议跨年龄层比较时同时报告两组数据，避免单独依赖任一年龄层得出剂量反应结论。",
        ],
        ["", ""],
        ["生成日期", "2026-09-11"],
        ["生成脚本", "scripts/extract_p1_naive_seroconversion.py"],
    ]
    for r, (k, v) in enumerate(lines, 1):
        a = ws.cell(row=r, column=1, value=k)
        b = ws.cell(row=r, column=2, value=v)
        a.alignment = Alignment(vertical="top", wrap_text=True)
        b.alignment = Alignment(vertical="top", wrap_text=True)
        a.font = Font(bold=True) if k else Font()
        a.border = BORDER
        b.border = BORDER
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 95


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
DOC = None  # 全局 docx 对象，供各函数访问


def main():
    global DOC
    DOC = Document(str(DOCX_T1))

    print("=" * 72)
    print("【数据源】第 1 册 14.2.1.4 / 14.2.1.5 / 14.2.1.6 章节官方汇总表")
    print("【处理】直接读取，不重新计算")
    print("=" * 72)

    # 打印 GMC 表前几行做交叉验证
    print("\n===== GMC 验证（14.2.1.5 18-59岁 M1 FAS T194 R11）=====")
    gmc_m1_18_59 = read_gmc_table(DOC, 194)
    for gi, grp in enumerate(GROUPS):
        r = gmc_m1_18_59[gi]
        print(f"  {grp:<10} N={r['n_neg']}  GMC={r['gmc']}  CI={r['gmc_ci']}")

    print("\n===== 阳转率验证（14.2.1.4 全体 M1 FAS T147 R6/R8）=====")
    scr_m1_all = read_scr_table(DOC, 147)
    for gi, grp in enumerate(GROUPS):
        r = scr_m1_all[gi]
        print(
            f"  {grp:<10} 阳转数={r['n_sero']}/{r['den_n']}  阳转率={r['scr_pct']:.2f}%  CI={r['ci']}"
        )

    print("\n" + "=" * 72)
    print("【输出】")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Sheet1: GMC_FAS
    ws1 = wb.create_sheet()
    write_gmc_sheet(ws1, "FAS")
    print("  Sheet1 = 每组未校正GMC_FAS_无接种史")

    # Sheet2: GMC_PPS
    ws2 = wb.create_sheet()
    write_gmc_sheet(ws2, "PPS")
    print("  Sheet2 = 每组未校正GMC_PPS_无接种史")

    # Sheet3: FAS 阳转率
    ws3 = wb.create_sheet()
    write_scr_sheet(ws3, "FAS")
    print("  Sheet3 = FAS_无接种史阳转率")

    # Sheet4: PPS 阳转率
    ws4 = wb.create_sheet()
    write_scr_sheet(ws4, "PPS")
    print("  Sheet4 = PPS_无接种史阳转率")

    # Sheet5: 方法说明
    ws5 = wb.create_sheet()
    write_methodology_sheet(ws5)
    print("  Sheet5 = 口径与方法说明")

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"\n✅ 已写出: {OUT_XLSX}")


if __name__ == "__main__":
    main()
