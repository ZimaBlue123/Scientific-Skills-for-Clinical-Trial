#!/usr/bin/env python3
"""
build_sae_listing_workbook.py

Build a combined SAE (严重不良事件) listing workbook for the recombinant
hepatitis B vaccine (Hansenula polymorpha, CpG + aluminium adjuvant) Phase 1 and
Phase 2 trials, from the TFL listing volumes under review_materials/统计/.

Sources (subject-level SAE listings in the TFL):
  * Ⅰ期 第9册（清单1）  表16.2.7.4  严重不良事件清单(SS)
  * Ⅰ期 第10册（清单2） 表16.2.8.3.2 新生儿严重不良事件清单(SS)   -> 无相关数据
  * Ⅱ期 第10册（清单3） 表16.2.7.4  严重不良事件清单(SS)
  * Ⅱ期 第10册（清单3） 表16.2.8.2.1 新生儿严重不良事件清单(SS)   -> 无相关数据

Rules honoured:
  * every field is copied verbatim from the TFL (no inference, no rewriting);
  * 相关性判定原因 is left EMPTY because the TFL listings carry no such column
    (the SARs only give aggregate counts and a definition of 有关/无关, no
    per-case rationale);
  * an extra derived column 相关性归类（按SAR定义） applies the SAR's own
    definition (肯定有关/很可能有关/可能有关/缺失 -> 有关;
    可能无关/肯定无关/无关 -> 无关).

Output: review_materials/统计/SAE清单_Ⅰ期+Ⅱ期.xlsx
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
STAT_DIR = ROOT / "review_materials" / "统计"
OUT_XLSX = STAT_DIR / "SAE清单_Ⅰ期+Ⅱ期.xlsx"

# ----------------------------------------------------------------------------
# Source definitions
# ----------------------------------------------------------------------------
SOURCES = [
    {
        "phase": "Ⅰ期",
        "vol": "第9册（清单1）",
        "file": STAT_DIR
        / "TFL-Phase1"
        / "远大赛威信-重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅰ期统计分析报告-第9册（清单1）.docx",
        "table": "表16.2.7.4 严重不良事件清单(SS)",
        "kind": "subject",
    },
    {
        "phase": "Ⅰ期",
        "vol": "第10册（清单2）",
        "file": STAT_DIR
        / "TFL-Phase1"
        / "远大赛威信-重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅰ期统计分析报告-第10册（清单2）.docx",
        "table": "表16.2.8.3.2 新生儿严重不良事件清单(SS)",
        "kind": "neonate",
    },
    {
        "phase": "Ⅱ期",
        "vol": "第10册（清单3）",
        "file": STAT_DIR
        / "TFL-Phase2"
        / "YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第10册(清单3).docx",
        "table": "表16.2.7.4 严重不良事件清单(SS)",
        "kind": "subject",
    },
    {
        "phase": "Ⅱ期",
        "vol": "第10册（清单3）",
        "file": STAT_DIR
        / "TFL-Phase2"
        / "YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第10册(清单3).docx",
        "table": "表16.2.8.2.1 新生儿严重不良事件清单(SS)",
        "kind": "neonate",
    },
]

# ----------------------------------------------------------------------------
# Column layouts as they appear in each listing
# ----------------------------------------------------------------------------
P1_COLS = [
    "序号",
    "不良事件描述",
    "系统器官分类",
    "首选术语",
    "是否TESAE",
    "严重程度",
    "SAE开始日期//SAE结束日期",
    "转归情况",
    "治疗情况",
    "相关性",
    "SAE分类",
    "死亡日期",
    "是否AESI",
    "是否导致退出",
]
P2_COLS = [
    "序号",
    "SAE描述",
    "系统器官分类//首选术语",
    "SAE开始日期//SAE结束日期",
    "发生剂次",
    "发生时间(天)",
    "持续时间(天)",
    "严重程度",
    "转归情况",
    "相关性",
    "SAE导致",
    "是否导致提前退出",
]

RELATED = {"肯定有关", "很可能有关", "可能有关"}
UNRELATED_P1 = {"可能无关", "肯定无关"}
UNRELATED_P2 = {"可能无关", "无关"}

SUBJECT_KEYS = {
    "组别": "组别",
    "年龄组": "年龄组",
    "受试者编号": "受试者编号",
    "研究编号": "受试者编号",
    "年龄(岁)": "年龄(岁)",
    "性别": "性别",
    "第1剂接种日期": "第1剂接种日期",
    "第2剂接种日期": "第2剂接种日期",
    "第3剂接种日期": "第3剂接种日期",
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def qn(tag: str) -> str:
    return tag


def row_logical_texts(row) -> list[str]:
    """Cell texts for a row, collapsing ONLY horizontally merged repeats.

    ``row.cells`` repeats merged cells, so a naive de-duplication by text would
    wrongly drop two adjacent cells that legitimately hold the same value
    (e.g. 是否AESI="否" and 是否导致退出="否"). Compare by element identity
    instead of by text.
    """
    out: list[str] = []
    prev_tc = None
    for cell in row.cells:
        tc = cell._tc
        if tc is prev_tc:
            continue
        prev_tc = tc
        out.append(clean(cell.text))
    return out


def find_table(doc: Document, caption_key: str) -> Table | None:
    caption = ""
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            txt = clean(Paragraph(child, doc).text)
            if txt:
                caption = txt
            continue
        if isinstance(child, CT_Tbl):
            if caption_key in caption:
                return Table(child, doc)
            caption = ""
    return None


def parse_subject_line(line: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for part in line.split("，"):
        if "：" not in part:
            continue
        key, val = part.split("：", 1)
        key = key.strip()
        if key in SUBJECT_KEYS:
            info[SUBJECT_KEYS[key]] = val.strip()
    return info


def split_dates(value: str) -> tuple[str, str]:
    if "//" in value:
        start, end = value.split("//", 1)
        return start.strip(), end.strip()
    parts = value.split("/")
    if len(parts) == 2 and len(parts[0]) >= 8:
        return parts[0].strip(), parts[1].strip()
    return value.strip(), ""


def split_soc_pt(value: str) -> tuple[str, str]:
    if "//" in value:
        soc, pt = value.split("//", 1)
        return soc.strip(), pt.strip()
    return value.strip(), ""


def classify_relation(phase: str, value: str) -> str:
    v = value.strip()
    if not v:
        return "缺失（按SAR定义归为“有关”）"
    if v in RELATED:
        return "有关"
    if phase == "Ⅰ期" and v in UNRELATED_P1:
        return "无关"
    if phase == "Ⅱ期" and v in UNRELATED_P2:
        return "无关"
    return "未定义术语"


def build_rows() -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    notes: list[str] = []

    for src in SOURCES:
        path: Path = src["file"]
        if not path.exists():
            notes.append(f"!! 缺失文件: {path}")
            continue
        print(f"opening {path.name} [{src['table']}] ...", file=sys.stderr)
        doc = Document(str(path))
        table = find_table(doc, src["table"].split(" ", 1)[0])
        if table is None:
            notes.append(f"!! 未找到: {src['phase']} {src['table']}")
            continue

        ncols = len(table.columns)
        subject: dict[str, str] = {}
        data_count = 0

        for r_idx, row in enumerate(table.rows):
            if r_idx == 0:  # column header row
                continue
            texts = row_logical_texts(row)
            if not any(texts):  # fully blank spacer row
                continue

            # subject banner row / footnote row -> single merged cell
            if len(texts) <= 1:
                text = texts[0] if texts else ""
                if "：" in text and ("组别" in text or "年龄组" in text):
                    subject = parse_subject_line(text)
                elif "无相关数据" in text:
                    notes.append(f"{src['phase']} {src['table']}：无相关数据。")
                continue

            texts = (texts + [""] * ncols)[:ncols]
            if src["kind"] == "neonate":
                notes.append(
                    f"{src['phase']} {src['table']}：检测到非预期的明细行 -> {' | '.join(texts)}"
                )
                continue

            if src["phase"] == "Ⅰ期":
                values = dict(zip(P1_COLS, texts, strict=False))
                start, end = split_dates(values.get("SAE开始日期//SAE结束日期", ""))
                rec = {
                    "期别": "Ⅰ期",
                    "数据来源": f"{src['vol']} {src['table']}",
                    "年龄组": subject.get("年龄组", ""),
                    "组别": subject.get("组别", ""),
                    "受试者编号": subject.get("受试者编号", ""),
                    "性别": subject.get("性别", ""),
                    "年龄(岁)": subject.get("年龄(岁)", ""),
                    "第1剂接种日期": subject.get("第1剂接种日期", ""),
                    "第2剂接种日期": subject.get("第2剂接种日期", ""),
                    "第3剂接种日期": subject.get("第3剂接种日期", ""),
                    "SAE序号": values.get("序号", ""),
                    "SAE描述": values.get("不良事件描述", ""),
                    "系统器官分类(SOC)": values.get("系统器官分类", ""),
                    "首选术语(PT)": values.get("首选术语", ""),
                    "是否TESAE": values.get("是否TESAE", ""),
                    "发生剂次": "",
                    "发生时间(天)": "",
                    "持续时间(天)": "",
                    "SAE开始日期": start,
                    "SAE结束日期": end,
                    "严重程度": values.get("严重程度", ""),
                    "转归情况": values.get("转归情况", ""),
                    "治疗情况": values.get("治疗情况", ""),
                    "相关性判定": values.get("相关性", ""),
                    "相关性判定原因": "",  # TFL 未提供 -> 留空
                    "SAE分类/SAE导致": values.get("SAE分类", ""),
                    "死亡日期": values.get("死亡日期", ""),
                    "是否AESI": values.get("是否AESI", ""),
                    "是否导致退出": values.get("是否导致退出", ""),
                }
            else:
                values = dict(zip(P2_COLS, texts, strict=False))
                start, end = split_dates(values.get("SAE开始日期//SAE结束日期", ""))
                soc, pt = split_soc_pt(values.get("系统器官分类//首选术语", ""))
                rec = {
                    "期别": "Ⅱ期",
                    "数据来源": f"{src['vol']} {src['table']}",
                    "年龄组": subject.get("年龄组", ""),
                    "组别": subject.get("组别", ""),
                    "受试者编号": subject.get("受试者编号", ""),
                    "性别": subject.get("性别", ""),
                    "年龄(岁)": subject.get("年龄(岁)", ""),
                    "第1剂接种日期": subject.get("第1剂接种日期", ""),
                    "第2剂接种日期": subject.get("第2剂接种日期", ""),
                    "第3剂接种日期": subject.get("第3剂接种日期", ""),
                    "SAE序号": values.get("序号", ""),
                    "SAE描述": values.get("SAE描述", ""),
                    "系统器官分类(SOC)": soc,
                    "首选术语(PT)": pt,
                    "是否TESAE": "",
                    "发生剂次": values.get("发生剂次", ""),
                    "发生时间(天)": values.get("发生时间(天)", ""),
                    "持续时间(天)": values.get("持续时间(天)", ""),
                    "SAE开始日期": start,
                    "SAE结束日期": end,
                    "严重程度": values.get("严重程度", ""),
                    "转归情况": values.get("转归情况", ""),
                    "治疗情况": "",
                    "相关性判定": values.get("相关性", ""),
                    "相关性判定原因": "",  # TFL 未提供 -> 留空
                    "SAE分类/SAE导致": values.get("SAE导致", ""),
                    "死亡日期": "",
                    "是否AESI": "",
                    "是否导致退出": values.get("是否导致提前退出", ""),
                }
            rec["相关性归类（按SAR定义）"] = classify_relation(src["phase"], rec["相关性判定"])
            records.append(rec)
            data_count += 1

        print(f"   -> {data_count} SAE rows", file=sys.stderr)

    return records, notes


# ----------------------------------------------------------------------------
# Workbook rendering
# ----------------------------------------------------------------------------
HEADERS = [
    "序号",
    "期别",
    "数据来源",
    "年龄组",
    "组别",
    "受试者编号",
    "性别",
    "年龄(岁)",
    "第1剂接种日期",
    "第2剂接种日期",
    "第3剂接种日期",
    "SAE序号",
    "SAE描述",
    "系统器官分类(SOC)",
    "首选术语(PT)",
    "是否TESAE",
    "发生剂次",
    "发生时间(天)",
    "持续时间(天)",
    "SAE开始日期",
    "SAE结束日期",
    "严重程度",
    "转归情况",
    "治疗情况",
    "相关性判定",
    "相关性判定原因",
    "相关性归类（按SAR定义）",
    "SAE分类/SAE导致",
    "死亡日期",
    "是否AESI",
    "是否导致退出",
]

WIDTHS = {
    "序号": 6,
    "期别": 7,
    "数据来源": 34,
    "年龄组": 12,
    "组别": 22,
    "受试者编号": 12,
    "性别": 6,
    "年龄(岁)": 9,
    "第1剂接种日期": 14,
    "第2剂接种日期": 14,
    "第3剂接种日期": 14,
    "SAE序号": 9,
    "SAE描述": 52,
    "系统器官分类(SOC)": 26,
    "首选术语(PT)": 22,
    "是否TESAE": 10,
    "发生剂次": 10,
    "发生时间(天)": 11,
    "持续时间(天)": 11,
    "SAE开始日期": 14,
    "SAE结束日期": 14,
    "严重程度": 10,
    "转归情况": 16,
    "治疗情况": 12,
    "相关性判定": 13,
    "相关性判定原因": 22,
    "相关性归类（按SAR定义）": 22,
    "SAE分类/SAE导致": 30,
    "死亡日期": 12,
    "是否AESI": 10,
    "是否导致退出": 13,
}

HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10)
REL_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[1].height = 32


def write_listing(ws, records: list[dict]) -> None:
    ws.append(HEADERS)
    style_header(ws, len(HEADERS))
    for i, rec in enumerate(records, start=1):
        row = [i] + [rec.get(h, "") for h in HEADERS[1:]]
        ws.append(row)
        r = ws.max_row
        for c in range(1, len(HEADERS) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=HEADERS[c - 1]
                in ("SAE描述", "系统器官分类(SOC)", "数据来源", "SAE分类/SAE导致"),
            )
        # highlight the causality columns
        for name in ("相关性判定", "相关性判定原因", "相关性归类（按SAR定义）"):
            ws.cell(row=r, column=HEADERS.index(name) + 1).fill = REL_FILL

    for c, h in enumerate(HEADERS, start=1):
        ws.column_dimensions[get_column_letter(c)].width = WIDTHS.get(h, 14)
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{ws.max_row}"


def write_summary(ws, records: list[dict]) -> None:
    ws.append(["期别", "相关性判定", "例次数", "占比(%)"])
    style_header(ws, 4)
    order = ["肯定有关", "很可能有关", "可能有关", "可能无关", "肯定无关", "无关"]
    for phase in ("Ⅰ期", "Ⅱ期"):
        subset = [r for r in records if r["期别"] == phase]
        total = len(subset)
        seen = set()
        for val in order:
            n = len([r for r in subset if r["相关性判定"] == val])
            if n == 0:
                continue
            seen.add(val)
            ws.append([phase, val, n, round(n * 100.0 / total, 2) if total else 0])
        other = [r for r in subset if r["相关性判定"] and r["相关性判定"] not in seen]
        if other:
            ws.append([phase, "其他/缺失", len(other), round(len(other) * 100.0 / total, 2)])
        ws.append([phase, "合计", total, 100.0 if total else 0])
        ws.append([])
    for c, w in zip(range(1, 5), (12, 18, 10, 10), strict=False):
        ws.column_dimensions[get_column_letter(c)].width = w
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=4):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER


def write_notes(ws, records: list[dict], notes: list[str]) -> None:
    ws.append(["项目", "说明"])
    style_header(ws, 2)
    n1 = len([r for r in records if r["期别"] == "Ⅰ期"])
    n2 = len([r for r in records if r["期别"] == "Ⅱ期"])
    subj1 = len({r["受试者编号"] for r in records if r["期别"] == "Ⅰ期"})
    subj2 = len({r["受试者编号"] for r in records if r["期别"] == "Ⅱ期"})
    items = [
        ("清单内容", "重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅰ期、Ⅱ期全部严重不良事件（SAE）"),
        ("生成日期", date.today().isoformat()),
        ("Ⅰ期 SAE 例次数", f"{n1}（涉及受试者 {subj1} 例）"),
        ("Ⅱ期 SAE 例次数", f"{n2}（涉及受试者 {subj2} 例）"),
        ("Ⅰ期数据来源", "TFL-Phase1 第9册（清单1）表16.2.7.4 严重不良事件清单(SS)"),
        ("Ⅱ期数据来源", "TFL-Phase2 第10册（清单3）表16.2.7.4 严重不良事件清单(SS)"),
        (
            "新生儿SAE",
            "Ⅰ期表16.2.8.3.2、Ⅱ期表16.2.8.2.1 新生儿严重不良事件清单均为“无相关数据”，故未纳入清单。",
        ),
        ("相关性判定", "直接照抄 TFL 清单中的“相关性”列原文。"),
        (
            "相关性判定原因",
            "TFL 清单未提供判定原因列，Ⅰ期/Ⅱ期 SAR 亦仅给出汇总例次与“有关/无关”定义，无逐例判定依据，故本列全部留空。",
        ),
        (
            "相关性归类（按SAR定义）",
            "依据 SAR 脚注机械归类：Ⅰ期——“肯定有关/很可能有关/可能有关/缺失”为有关，“可能无关/肯定无关”为无关；"
            "Ⅱ期——“肯定有关/很可能有关/可能有关/缺失”为有关，“可能无关/无关”为无关。该列为按既定规则的推导，非原文数据。",
        ),
        ("数据完整性", "所有字段均逐字复制自 TFL，未做任何推断、改写或补全；原文为空者保留为空。"),
        (
            "计数口径",
            "同一 SAE 按 TFL 中不同首选术语（PT）拆分为多行，故“例次数”可能大于受试者例数。",
        ),
        ("MedDRA 版本", "Ⅰ期：MedDRA 27.1；Ⅱ期：MedDRA 28.1（TFL 脚注）。"),
        ("Ⅱ期时点范围", "Ⅱ期为基础阶段统计分析报告（TFL 第10册清单3），未包含免后12个月补充分析。"),
    ]
    for k, v in items:
        ws.append([k, v])
    if notes:
        ws.append([])
        ws.append(["扫描备注", "；".join(notes)])
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 110
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def main() -> int:
    records, notes = build_rows()
    if not records:
        print("no SAE records extracted", file=sys.stderr)
        return 1

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "SAE清单"
    write_listing(ws1, records)
    write_summary(wb.create_sheet("相关性判定汇总"), records)
    write_notes(wb.create_sheet("说明与数据来源"), records, notes)

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT_XLSX))
    print(f"OK -> {OUT_XLSX}  ({len(records)} SAE rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
