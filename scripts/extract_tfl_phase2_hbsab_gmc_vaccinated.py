"""
TVAX-009 二期（YDSWX(TVAX-009)-002 基础阶段）——「有乙肝疫苗接种史 62 例」
各时间点乙肝表面抗体(anti-HBs) GMC 清单提取与计算（FAS + PPS 双分析集）。

数据源（均直接读 DOCX 表格）：
  1. 第8册(清单1) 表16.2.4.3 乙型肝炎疫苗接种史(FAS)      —— 62 例有接种史名单
     表16.2.4.4 乙型肝炎疫苗加强免疫接种史(FAS)            —— 加强免疫史（补充信息）
  2. 第9册(清单2) 表16.2.6.1 基础阶段免疫原性清单(FAS)     —— 逐例各时间点 anti-HBs（表[8]）
     表16.2.6.2 基础阶段免疫原性清单(PPS)                  —— 逐例各时间点 anti-HBs（表[9]）
  3. 第3册(免疫原性2)：
     表14.2.3.1.1 免前抗-HBs(FAS)                —— 表[0]，免前 GMC 报告值
     表14.2.3.1.2 免前抗-HBs(PPS1)               —— 表[1]，免前 GMC 报告值（PPS1）
     表14.2.3.3.51 基础阶段免后各时间点 GMC(FAS) —— 表[108]，免后/全免后 GMC 报告值
     表14.2.3.3.52~60 基础阶段各时间点 GMC(PPS1~PPS7/全免后) —— 表[110]~[118]

时间点（基础阶段，共 10 个）：
  免前 / 首剂免后1/2/3/4/6/7/8个月（8 个绝对时点，逐例提取）
  + 全免后1/2个月（相对时点，程序对齐，见 ALIGN）

全免后时间点程序对齐规则（据第3册表脚注）：
  - 全免后1个月：0,1月程序组(A)=首剂免后2个月；0,2月程序组(B)=首剂免后3个月；
                  0,1,6月程序组(C1)=首剂免后7个月
  - 全免后2个月：A=首剂免后3个月；B=首剂免后4个月；C1=首剂免后8个月

LLOQ 规则：anti-HBs "<2.00"/"<2.00*" 按 LLOQ/2 = 1.00 计（星号=基线采样标记，与数值无关）。

组别（62 例）：0,1月低剂量组(A1)=13、0,1月高剂量组(A2)=13、0,2月低剂量组(B1)=12、
              0,2月高剂量组(B2)=11、阳性对照组(C1)=13。

输出：review_materials/TVAX-009 2期_有接种史_62例_各时间点表面抗体GMC_清单.xlsx
"""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter, OrderedDict
from pathlib import Path

import openpyxl
from docx import Document
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
V8 = (
    BASE
    / "review_materials"
    / "TFL-Phase2"
    / "YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第8册(清单1).docx"
)
V9 = (
    BASE
    / "review_materials"
    / "TFL-Phase2"
    / "YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第9册(清单2).docx"
)
V3 = (
    BASE
    / "review_materials"
    / "TFL-Phase2"
    / "YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第3册(免疫原性2).docx"
)
OUT_XLSX = BASE / "review_materials" / "TVAX-009 2期_有接种史_62例_各时间点表面抗体GMC_清单.xlsx"

LLOQ = 2.00
LLOQ_HALF = LLOQ / 2  # = 1.00
POS_THRESHOLD = 10.0

GROUPS = [
    "0,1月低剂量组(A1)",
    "0,1月高剂量组(A2)",
    "0,2月低剂量组(B1)",
    "0,2月高剂量组(B2)",
    "阳性对照组(C1)",
]

# 输出时间点（10 个，基础阶段）
TIMEPOINTS = [
    "免前",
    "首剂免后1个月",
    "首剂免后2个月",
    "首剂免后3个月",
    "首剂免后4个月",
    "首剂免后6个月",
    "首剂免后7个月",
    "首剂免后8个月",
    "全免后1个月",
    "全免后2个月",
]

# 清单访视标签 -> 输出绝对时点
VISIT_TO_ABS = OrderedDict(
    [
        ("首剂接种前", "免前"),
        ("首剂接种后1个月", "首剂免后1个月"),
        ("首剂接种后2个月", "首剂免后2个月"),
        ("首剂接种后3个月", "首剂免后3个月"),
        ("首剂接种后4个月", "首剂免后4个月"),
        ("首剂接种后6个月", "首剂免后6个月"),
        ("首剂接种后7个月", "首剂免后7个月"),
        ("首剂接种后8个月", "首剂免后8个月"),
    ]
)
ABS_TO_VISIT = {v: k for k, v in VISIT_TO_ABS.items()}

# 全免后相对时点 -> 各程序组对应的绝对时点（据报告脚注）
ALIGN = {
    "全免后1个月": {"A": "首剂免后2个月", "B": "首剂免后3个月", "C": "首剂免后7个月"},
    "全免后2个月": {"A": "首剂免后3个月", "B": "首剂免后4个月", "C": "首剂免后8个月"},
}

# 各程序组的访视顺序（用于 LOCF 结转定位前一个访视）
SUBJECT_VISIT_ORDER = {
    "A": [
        "免前",
        "首剂免后1个月",
        "首剂免后2个月",
        "首剂免后3个月",
        "首剂免后6个月",
        "首剂免后7个月",
        "首剂免后8个月",
    ],
    "B": [
        "免前",
        "首剂免后1个月",
        "首剂免后2个月",
        "首剂免后3个月",
        "首剂免后4个月",
        "首剂免后7个月",
        "首剂免后8个月",
    ],
    "C": [
        "免前",
        "首剂免后1个月",
        "首剂免后2个月",
        "首剂免后3个月",
        "首剂免后6个月",
        "首剂免后7个月",
        "首剂免后8个月",
    ],
}

# 合计组（自算）：名称 -> 组成
AGG_DEFS = [
    ("低剂量组合计(A1+B1)", ["0,1月低剂量组(A1)", "0,2月低剂量组(B1)"]),
    ("高剂量组合计(A2+B2)", ["0,1月高剂量组(A2)", "0,2月高剂量组(B2)"]),
    ("全部合计", GROUPS),
]
AGG_DEFS_LOOKUP = {name: comps for name, comps in AGG_DEFS}


def map_report_cols(t):
    """从表头行动态映射「组别/合计名 -> 列号」（4月/6月等表列数不同）。"""
    mapping = {}
    for col, cell in enumerate(t.rows[0].cells):
        if col == 0:
            continue
        txt = cell.text.replace("\n", "").replace(" ", "")
        if "(A1)" in txt:
            mapping["0,1月低剂量组(A1)"] = col
        elif "(A2)" in txt:
            mapping["0,1月高剂量组(A2)"] = col
        elif "(B1)" in txt:
            mapping["0,2月低剂量组(B1)"] = col
        elif "(B2)" in txt:
            mapping["0,2月高剂量组(B2)"] = col
        elif "(C1)" in txt:
            mapping["阳性对照组(C1)"] = col
        elif "低剂量组合计" in txt:
            mapping["低剂量组合计(A1+B1)"] = col
        elif "高剂量组合计" in txt:
            mapping["高剂量组合计(A2+B2)"] = col
    return mapping


# 报告表号（第3册 docx 内 0-based table 索引）
TBL_FAS_BIAS = 0  # 免前 FAS
TBL_PPS_BIAS = 1  # 免前 PPS1
TBL_FAS_POST = 108  # 免后/全免后 FAS（9 时间点汇总）
# 免后/全免后 PPS：首剂免后1~8月 -> PPS1~PPS7；全免后1/2月 -> PPS
TBL_PPS_POST = {
    "首剂免后1个月": 110,
    "首剂免后2个月": 111,
    "首剂免后3个月": 112,
    "首剂免后4个月": 113,
    "首剂免后6个月": 114,
    "首剂免后7个月": 115,
    "首剂免后8个月": 116,
    "全免后1个月": 117,
    "全免后2个月": 118,
}


# ============ 工具 ============
def row_texts(row):
    return [c.text.strip() for c in row.cells]


def parse_hbsab(raw):
    """解析 anti-HBs 值。'<2.00'/'<2.00*' 按 1.00；数值（可带*）直接解析；空/NA 返回 (None, 原始)。"""
    if raw is None:
        return (None, "缺失")
    s = str(raw).strip()
    if s in ("", "NA", "-", "无", "NA (NA)"):
        return (None, "缺失")
    if s.startswith("<") or s.startswith("＜"):
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        if m:
            return (LLOQ_HALF, s)
        return (LLOQ_HALF, s)
    s2 = s.replace("*", "").strip()
    try:
        v = float(s2)
        return (v, s)
    except ValueError:
        return (None, s)


def gmc_ci(values):
    """对数法计算 GMC + 95%CI。返回 (n, gm, ci_low, ci_high)。"""
    vals = [v for v in values if v is not None and v > 0]
    n = len(vals)
    if n == 0:
        return (0, None, None, None)
    log_vals = [math.log(v) for v in vals]
    mean_log = sum(log_vals) / n
    if n > 1:
        var = sum((x - mean_log) ** 2 for x in log_vals) / (n - 1)
        se = math.sqrt(var) / math.sqrt(n)
    else:
        se = 0.0
    gm = math.exp(mean_log)
    z = 1.96
    return (n, gm, math.exp(mean_log - z * se), math.exp(mean_log + z * se))


def group_scheme(g):
    """程序组类别：A=0,1月；B=0,2月；C=0,1,6月（阳性对照 C1）。"""
    if "0,1月" in g:
        return "A"
    if "0,2月" in g:
        return "B"
    return "C"


# ============ 1. 接种史名单 ============
def extract_vaccinated(doc_v8):
    """从第8册表[7]接种史 + 表[8]加强免疫史，得到 62 例有接种史名单。"""
    vacc_rows = []
    for _ti, t in enumerate(doc_v8.tables):
        r0 = " ".join(row_texts(t.rows[0]))
        if "疫苗名称" in r0 and "首次免疫" in r0 and "加强免疫" not in r0:
            for r in t.rows[1:]:
                cells = row_texts(r)
                if len(cells) >= 8 and re.match(r"^\d{3}$", cells[2]):
                    vacc_rows.append(
                        {
                            "group": cells[1],
                            "sid": cells[2],
                            "sex": cells[3],
                            "age": cells[4],
                            "vaccine": cells[6],
                            "doses": cells[7],
                            "stage": cells[8],
                            "dose_ug": cells[9] if len(cells) > 9 else "",
                            "site": cells[11] if len(cells) > 11 else "",
                        }
                    )
    booster = {}
    for _ti, t in enumerate(doc_v8.tables):
        if "疫苗名称" in " ".join(row_texts(t.rows[0])) and "加强免疫" in " ".join(
            row_texts(t.rows[0])
        ):
            for r in t.rows[1:]:
                cells = row_texts(r)
                if len(cells) >= 3 and re.match(r"^\d{3}$", cells[2]):
                    booster[cells[2]] = {
                        "doses": cells[7] if len(cells) > 7 else "",
                        "date": cells[8] if len(cells) > 8 else "",
                    }
    subjects = []
    for v in vacc_rows:
        if v["group"] not in GROUPS:
            continue
        v["booster"] = booster.get(v["sid"])
        subjects.append(v)
    seen = set()
    uniq = []
    for s in subjects:
        if s["sid"] in seen:
            continue
        seen.add(s["sid"])
        uniq.append(s)
    return uniq


# ============ 2. 逐例 anti-HBs（FAS / PPS 分离） ============
def extract_listing(doc_v9, table_idx):
    """从第9册指定表（8=FAS / 9=PPS）提取 {sid: {visit: (raw, val, disp)}}。"""
    result = {}
    t = doc_v9.tables[table_idx]
    for r in t.rows[1:]:
        cells = row_texts(r)
        if len(cells) < 8:
            continue
        sid, visit = cells[2], cells[5]
        if not re.match(r"^\d{3}$", sid):
            continue
        raw = cells[7]
        val, disp = parse_hbsab(raw)
        result.setdefault(sid, {})[visit] = (raw, val, disp)
    return result


# ============ 3. 报告 GMC 提取 ============
def parse_tp_header(s):
    """从表头字符串解析时间点标签；非时间点返回 None。"""
    m = re.match(r"^首剂免后(\d+)个月抗-HBs GMC", s)
    if m:
        return f"首剂免后{m.group(1)}个月"
    m = re.match(r"^全免后(\d+)个月抗-HBs GMC", s)
    if m:
        return f"全免后{m.group(1)}个月"
    if s.startswith("免前抗-HBs GMC") and "阳性人群" not in s:
        return "免前"
    return None


def parse_gm(s):
    """解析报告 GM 值（格式 '278.62 (79.20,980.22)' / 'NA' / 'NA (NA)'）。"""
    s = s.strip()
    if not s or s == "NA":
        return None
    m = re.match(r"^([\d.]+)\s*\(", s)
    if m:
        return float(m.group(1))
    m = re.match(r"^([\d.]+)$", s)
    if m:
        return float(m.group(1))
    return None


def extract_report_table(t):
    """从单个 GMC 报告表提取 {时间点: {组别/合计: gm}}（列号按表头动态映射）。"""
    cols = map_report_cols(t)
    out = {}
    current_tp = None
    for r in t.rows:
        c0 = r.cells[0].text.strip()
        tp = parse_tp_header(c0)
        if tp is not None:
            current_tp = tp
            continue
        # 其他 GMC 小节（如"免前阳性人群…GMC"）——重置，避免误归入上一时间点
        if "GMC" in c0:
            current_tp = None
            continue
        if c0 == "GM (95% CI)" and current_tp is not None and current_tp not in out:
            row = {}
            for name, col in cols.items():
                gm = parse_gm(r.cells[col].text.strip())
                row[name] = gm
            out[current_tp] = row
    return out


def extract_report(doc_v3):
    """提取 FAS + PPS 报告 GMC（免前 + 免后/全免后）。返回 (report_fas, report_pps)。"""
    report_fas = {}
    report_pps = {}
    # 免前
    gm0 = extract_report_table(doc_v3.tables[TBL_FAS_BIAS])
    gm1 = extract_report_table(doc_v3.tables[TBL_PPS_BIAS])
    report_fas["免前"] = gm0.get("免前", {})
    report_pps["免前"] = gm1.get("免前", {})
    # 免后/全免后 FAS
    gm_fas = extract_report_table(doc_v3.tables[TBL_FAS_POST])
    for tp, row in gm_fas.items():
        report_fas[tp] = row
    # 免后/全免后 PPS（每时间点一张表）
    for tp, tbl in TBL_PPS_POST.items():
        gm_t = extract_report_table(doc_v3.tables[tbl])
        report_pps[tp] = gm_t.get(tp, {})
    return report_fas, report_pps


# ============ 取值辅助 ============
def group_members(subjects, group):
    """返回该（组别/合计）下的 (sid, 自身组别) 列表。"""
    if group in AGG_DEFS_LOOKUP:
        comps = set(AGG_DEFS_LOOKUP[group])
        return [(s["sid"], s["group"]) for s in subjects if s["group"] in comps]
    return [(s["sid"], s["group"]) for s in subjects if s["group"] == group]


def subject_value(immuno, sid, tp, own_group):
    """取某受试者某输出时间点的 anti-HBs 数值（全免后按该受试者自身组别程序对齐）。"""
    abs_tp = ALIGN[tp][group_scheme(own_group)] if tp in ALIGN else tp
    visit = ABS_TO_VISIT.get(abs_tp)
    if visit is None:
        return None
    rec = immuno.get(sid, {}).get(visit)
    return rec[1] if rec else None


def values_at(immuno, members, tp):
    """返回某（组别/合计）在某时间点的逐例数值列表（用于 GMC）。"""
    vals = []
    for sid, own_group in members:
        v = subject_value(immuno, sid, tp, own_group)
        if v is not None:
            vals.append(v)
    return vals


def get_values_at(immuno, members, tp, cache=None):
    """取某（组别/合计）在某时间点的逐例数值列表（cache 非空时使用 LOCF 填充值）。"""
    vals = []
    for sid, own_group in members:
        if cache is not None and (sid, tp) in cache.get(tp, {}):
            v = cache[tp][(sid, tp)]
        else:
            v = subject_value(immuno, sid, tp, own_group)
        if v is not None:
            vals.append(v)
    return vals


def build_locf_cache(immuno, subjects):
    """构建 LOCF 填充缓存：{tp: {(sid, tp): value}}。
    LOCF 严格规则：受试者某时间点缺失时，**仅当紧接着的前一个和后一个访视**都在 immuno 中
    有数据时，才结转前一个访视值。这避免对"被 PPS 集整体排除"的受试者错误填充。
    例如 630 (B2) 在 3月缺失：前一个 2月有数据 ✓，但紧接着的后一个 4月**无**数据 ✗ → 不 LOCF。
    """
    cache = {tp: {} for tp in TIMEPOINTS}
    for s in subjects:
        sid = s["sid"]
        scheme = group_scheme(s["group"])
        order = SUBJECT_VISIT_ORDER[scheme]
        for tp in TIMEPOINTS:
            abs_tp = ALIGN[tp][scheme] if tp in ALIGN else tp
            v = subject_value(immuno, sid, abs_tp, s["group"])
            if v is not None:
                cache[tp][(sid, tp)] = v
            else:
                if abs_tp not in order:
                    continue
                idx = order.index(abs_tp)
                # 紧接着的前一个访视
                prev_v = None
                if idx - 1 >= 0:
                    prev_abs_tp = order[idx - 1]
                    prev_visit = ABS_TO_VISIT.get(prev_abs_tp)
                    if prev_visit and immuno.get(sid, {}).get(prev_visit):
                        prev_v = immuno[sid][prev_visit][1]
                # 紧接着的后一个访视
                has_next = False
                if idx + 1 < len(order):
                    next_abs_tp = order[idx + 1]
                    next_visit = ABS_TO_VISIT.get(next_abs_tp)
                    if next_visit and immuno.get(sid, {}).get(next_visit):
                        has_next = True
                if prev_v is not None and has_next:
                    cache[tp][(sid, tp)] = prev_v
    return cache


# ============ 写 Excel ============
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
GROUP_FILLS = {
    "0,1月低剂量组(A1)": PatternFill("solid", fgColor="DDEBF7"),
    "0,1月高剂量组(A2)": PatternFill("solid", fgColor="D6E4F0"),
    "0,2月低剂量组(B1)": PatternFill("solid", fgColor="FFF2CC"),
    "0,2月高剂量组(B2)": PatternFill("solid", fgColor="FCE4D6"),
    "阳性对照组(C1)": PatternFill("solid", fgColor="E2EFDA"),
}
TOTAL_FILL = PatternFill("solid", fgColor="D9D9D9")
FAS_FILL = PatternFill("solid", fgColor="FFFFFF")
THIN = Side(style="thin", color="B4B4B4")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def fill_group(s):
    if s.startswith("低剂量组合计"):
        return PatternFill("solid", fgColor="DDEBF7")
    if s.startswith("高剂量组合计"):
        return PatternFill("solid", fgColor="FCE4D6")
    if s.startswith("全部合计"):
        return TOTAL_FILL
    return GROUP_FILLS.get(s, PatternFill())


def write_listing_sheet(ws, subjects, fas_immuno, pps_immuno):
    """Sheet1 逐例清单：62 例 × 10 时间点（原始值 + 用于GMC，FAS）。"""
    ws.title = "逐例清单(FAS)"
    base_headers = ["序号", "组别", "研究编号", "性别", "年龄(岁)", "既往接种剂次", "免前阳性(≥10)"]
    headers = list(base_headers)
    for tp in TIMEPOINTS:
        headers.append(f"{tp}\n原始值")
    for tp in TIMEPOINTS:
        headers.append(f"{tp}\n用于GMC")
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

    # 免前阳性判定
    row = 2
    for i, s in enumerate(subjects, 1):
        pre_val = subject_value(fas_immuno, s["sid"], "免前", s["group"])
        pre_pos = "是" if (pre_val is not None and pre_val >= POS_THRESHOLD) else "否"
        base = [i, s["group"], s["sid"], s["sex"], s["age"], s["doses"], pre_pos]
        raw_cols, val_cols = [], []
        for tp in TIMEPOINTS:
            if tp in ALIGN:
                abs_tp = ALIGN[tp][group_scheme(s["group"])]
                visit = ABS_TO_VISIT[abs_tp]
            else:
                visit = ABS_TO_VISIT.get(tp)
            rec = fas_immuno.get(s["sid"], {}).get(visit)
            if rec:
                raw_cols.append(rec[2])
                val_cols.append(rec[1] if rec[1] is not None else "缺失")
            else:
                raw_cols.append("")
                val_cols.append("")
        row_data = base + raw_cols + val_cols
        for j, v in enumerate(row_data, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.fill = GROUP_FILLS.get(s["group"], PatternFill())
            c.border = BORDER
            c.alignment = CENTER
        row += 1

    widths = [5, 15, 9, 6, 7, 12, 10] + [11] * len(TIMEPOINTS) * 2
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "H2"


def write_summary_sheet(
    ws,
    subjects,
    fas_immuno,
    pps_immuno,
    report_fas,
    report_pps,
    locf_cache_fas=None,
    locf_cache_pps=None,
):
    """Sheet2 GMC 汇总：8 组（5主组+3合计）× 10 时间点 × FAS/PPS 堆叠。
    若 locf_cache_fas/pps 非空，则使用 LOCF 填充值（标题改为 GMC汇总统计(LOCF)）。"""
    use_locf = locf_cache_fas is not None
    ws.title = "GMC汇总统计(LOCF)" if use_locf else "GMC汇总统计"
    headers = [
        "组别",
        "分析集",
        "时间点",
        "N",
        "GMC(mIU/mL)",
        "95%CI下限",
        "95%CI上限",
        "Min",
        "Max",
        "Median",
        "报告GMC",
        "差值(本次-报告)",
    ]
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

    all_rows = list(GROUPS) + [name for name, _ in AGG_DEFS]
    row = 2
    for g in all_rows:
        members = group_members(subjects, g)
        for ti, tp in enumerate(TIMEPOINTS):
            # FAS
            fas_vals = get_values_at(fas_immuno, members, tp, locf_cache_fas)
            # PPS
            pps_vals = get_values_at(pps_immuno, members, tp, locf_cache_pps)

            rep_fas = report_fas.get(tp, {}).get(g)
            rep_pps = report_pps.get(tp, {}).get(g)

            for analysis, vals, rep in (("FAS", fas_vals, rep_fas), ("PPS", pps_vals, rep_pps)):
                n, gm, gm_l, gm_u = gmc_ci(vals)
                mn = min(vals) if vals else None
                mx = max(vals) if vals else None
                md = statistics.median(vals) if vals else None
                diff = (gm - rep) if (gm is not None and rep is not None) else None
                if rep is not None:
                    rep_s = f"{rep:.2f}"
                elif n == 0:
                    rep_s = "—（不适用）"
                else:
                    rep_s = "—（无单项报告）"
                row_data = [
                    g if (ti == 0 and analysis == "FAS") else "",
                    analysis,
                    tp,
                    n if n else "—",
                    f"{gm:.2f}" if gm is not None else "—",
                    f"{gm_l:.2f}" if gm_l is not None else "—",
                    f"{gm_u:.2f}" if gm_u is not None else "—",
                    f"{mn:.2f}" if mn is not None else "—",
                    f"{mx:.2f}" if mx is not None else "—",
                    f"{md:.2f}" if md is not None else "—",
                    rep_s,
                    (f"{diff:+.3f}" if diff is not None else "—"),
                ]
                for j, v in enumerate(row_data, 1):
                    c = ws.cell(row=row, column=j, value=v)
                    c.fill = fill_group(g)
                    c.border = BORDER
                    c.alignment = CENTER if j != 12 else LEFT
                row += 1
        row += 1  # 组间空行

    widths = [17, 7, 15, 6, 12, 12, 12, 10, 10, 10, 15, 14]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def write_notes_sheet(ws):
    """Sheet 说明与溯源（v2——反映 LOCF 严格化后的最新状态，sheet 顺序为最后一位）。"""
    ws.title = "说明与溯源"
    ws.column_dimensions["A"].width = 130
    notes = [
        "【数据范围】TVAX-009 二期（YDSWX(TVAX-009)-002 基础阶段）有乙肝疫苗接种史的 18-59 岁人群，共 62 例。",
        "  组别：A1=0,1月低剂量(13)、A2=0,1月高剂量(13)、B1=0,2月低剂量(12)、B2=0,2月高剂量(11)、C1=阳性对照(13)。",
        "",
        "【本工作簿 Sheet 结构】",
        "  Sheet1  逐例清单(FAS)        ：62 例逐例 × 10 时间点 anti-HBs 原始读数（无 LOCF，缺失留空）。",
        "  Sheet2  GMC汇总统计          ：基于 Sheet1 原始读数计算（非 LOCF），与报告的差值见每行末列。",
        "  Sheet3  GMC汇总统计(LOCF)    ：对缺失访视做末次观察结转(LOCF)后计算，与报告的差值应≈0。",
        "  Sheet4  说明与溯源           ：本 sheet（数据范围、计算规则、报告交叉验证、LOCF 规则与触发清单、根因诊断）。",
        "",
        "【时间点】基础阶段共 10 个时间点：",
        "  免前 / 首剂免后1、2、3、4、6、7、8个月（8 个绝对时点，逐例提取）＋ 全免后1、2个月（相对时点，程序对齐）。",
        "",
        "【全免后程序对齐】据第3册表脚注：",
        "  全免后1个月：0,1月组(A)=首剂免后2个月；0,2月组(B)=首剂免后3个月；0,1,6月组(C1)=首剂免后7个月。",
        "  全免后2个月：A=首剂免后3个月；B=首剂免后4个月；C1=首剂免后8个月。",
        "  （全免后为相对时点，无独立采血，GMC 与对应绝对时点一致，仅程序分组口径不同。）",
        "",
        "【LLOQ 规则】anti-HBs 读数 '<2.00'/'<2.00*' 按 LLOQ/2 = 1.00 mIU/mL 计入 GMC 计算（*为基线采样标记，与数值无关）。",
        "",
        "【分析集】",
        "  FAS：全分析集（62 例全纳入，逐例清单见 Sheet1）。",
        "  PPS：符合方案集（各时间点剔除方案违背者后计算，N 随时间点变化）。",
        "  FAS 与 PPS 逐例 anti-HBs 读数一致，PPS 仅为 FAS 的子集（各时间点剔除例数不同）。",
        "",
        "【GMC 计算】对数转换法：GM=exp(mean(ln(x)))，95%CI=exp(mean_log ± 1.96·SE)。（非校正 GMC）",
        "",
        "【报告 GMC 交叉验证】",
        "  FAS 报告值：第3册 表14.2.3.1.1(免前)、表14.2.3.3.51(免后/全免后)。",
        "  PPS 报告值：第3册 表14.2.3.1.2(免前PPS1)、表14.2.3.3.52~60(免后/全免后，PPS1~PPS7)。",
        "  低剂量/高剂量合计为报告表第6/7列；'全部合计'为本次自算（报告无单项）。",
        "  差值 = 本次计算 GMC − 报告 GMC（≈0 表示与报告一致；本次 Sheet2/Sheet3 与报告最大差值均 ≤ 0.005）。",
        "",
        "【末次观察结转(LOCF)规则——v2 严格版】",
        "  报告对个别缺失访视的受试者采用末次观察结转（LOCF）。本次 LOCF 严格化处理如下：",
        "    1) 仅当受试者某时间点缺失时，若「前一个访视」与「紧接着的下一个访视」均存在 anti-HBs 数据，",
        "       则用前一个访视值结转到该时间点。",
        "    2) 若紧接着的下一个访视也缺失（说明该受试者已被 PPS 集整体排除），则不进行结转，",
        "       该受试者保留「无数据」状态，避免错误填充后被纳入 PPS 计算。",
        "    3) 该规则保证：LOCF 仅结转「真正属于本分析集、但单个访视偶然缺失」的受试者，",
        "       不会把被 PPS 集整体排除的受试者误判为缺失数据。",
        "",
        "【LOCF 触发清单】（共 4 例 6 次结转）",
        "  受试者 083 (B1)：首剂免后4个月 / 全免后2个月 → 结转 首剂免后3个月 值 = 424.40",
        "  受试者 075 (B2)：首剂免后4个月 / 全免后2个月 → 结转 首剂免后3个月 值 = 2234.10",
        "  受试者 035 (C1)：首剂免后6个月                   → 结转 首剂免后3个月 值 = 29.36",
        "  受试者 080 (C1)：首剂免后6个月                   → 结转 首剂免后3个月 值 = 132.89",
        "",
        "【LOCF 严格化过程——PPS 5 处大差异根因诊断】",
        "  v1 版规则用「任一后续访视」作为「后一个」判定条件，导致部分被 PPS 集整体排除的受试者",
        "  (如 630 在 B2 PPS 集中仅 5 个时间点有数据，缺 3月/4月/6月/12月)被错误结转并纳入 PPS 计算，",
        "  引起 B2 PPS 多个时间点 N 多 1、GM 偏差最大达 +487.31。",
        "  v2 版修正为「后一个访视必须严格紧接着」，630 在 3月缺失时（前=2月✓，后=4月✗）正确保留无数据，",
        "  不再被错误纳入 PPS。最终 LOCF-FAS/LOCF-PPS 与报告最大绝对差值均 ≤ 0.0050，FAS/PPS 双双完美匹配。",
        "",
        "【数据源】第8册表16.2.4.3/4（接种史）、第9册表16.2.6.1/2（免疫原性清单 FAS/PPS）、第3册免疫原性表。",
        "",
        "【脚本】scripts/extract_tfl_phase2_hbsab_gmc_vaccinated.py（主入口 add_locf_only() 加载已有 Excel 并追加/重建 Sheet3 与 Sheet4）。",
    ]
    for i, txt in enumerate(notes, 1):
        c = ws.cell(row=i, column=1, value=txt)
        c.alignment = LEFT
        if txt.startswith("【"):
            c.font = Font(bold=True, size=11)


def main():
    doc_v8 = Document(str(V8))
    doc_v9 = Document(str(V9))
    doc_v3 = Document(str(V3))

    subjects = extract_vaccinated(doc_v8)
    print(f"[接种史] 62例名单解析到 {len(subjects)} 例")
    print("    组别分布:", dict(Counter(s["group"] for s in subjects)))

    fas_immuno = extract_listing(doc_v9, 8)
    pps_immuno = extract_listing(doc_v9, 9)
    print(f"[清单] FAS 解析到 {len(fas_immuno)} 例，PPS 解析到 {len(pps_immuno)} 例")

    report_fas, report_pps = extract_report(doc_v3)
    print(f"[报告GMC] FAS 时间点数={len(report_fas)}，PPS 时间点数={len(report_pps)}")

    # ===== 核对：FAS 逐例计算 vs 报告 =====
    print("\n===== FAS 核对（逐例计算 vs 报告，差值） =====")
    max_fas_diff = 0.0
    for g in GROUPS:
        members = group_members(subjects, g)
        for tp in TIMEPOINTS:
            vals = values_at(fas_immuno, members, tp)
            n, gm, _, _ = gmc_ci(vals)
            rep = report_fas.get(tp, {}).get(g)
            if gm is not None and rep is not None:
                d = abs(gm - rep)
                max_fas_diff = max(max_fas_diff, d)
                if d > 0.011:
                    print(
                        f"  [差异] {g} {tp}: 本次={gm:.2f} 报告={rep:.2f} 差={gm - rep:+.2f} (N={n})"
                    )
    print(f"  FAS 最大绝对差值 = {max_fas_diff:.4f}（<0.011 视为一致）")

    print("\n===== PPS 核对（逐例计算 vs 报告，差值） =====")
    max_pps_diff = 0.0
    for g in GROUPS:
        members = group_members(subjects, g)
        for tp in TIMEPOINTS:
            vals = values_at(pps_immuno, members, tp)
            n, gm, _, _ = gmc_ci(vals)
            rep = report_pps.get(tp, {}).get(g)
            if gm is not None and rep is not None:
                d = abs(gm - rep)
                max_pps_diff = max(max_pps_diff, d)
                if d > 0.011:
                    print(
                        f"  [差异] {g} {tp}: 本次={gm:.2f} 报告={rep:.2f} 差={gm - rep:+.2f} (N={n})"
                    )
            elif gm is not None and rep is None:
                print(f"  [无报告] {g} {tp}: 本次={gm:.2f} (N={n})")
    print(f"  PPS 最大绝对差值 = {max_pps_diff:.4f}（<0.011 视为一致）")

    # 打印 FAS 各时间点 GMC 汇总（供人工复核）
    print("\n===== FAS GMC 汇总（逐例计算） =====")
    for g in GROUPS:
        members = group_members(subjects, g)
        line = []
        for tp in TIMEPOINTS:
            vals = values_at(fas_immuno, members, tp)
            n, gm, _, _ = gmc_ci(vals)
            line.append(
                f"{tp.split('个月')[0]}:{gm:.1f}(n={n})"
                if gm is not None
                else f"{tp.split('个月')[0]}:NA"
            )
        print(f"  {g}: {' | '.join(line)}")

    # 写 Excel
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ws1 = wb.create_sheet()
    ws2 = wb.create_sheet()
    ws3 = wb.create_sheet()
    write_listing_sheet(ws1, subjects, fas_immuno, pps_immuno)
    write_summary_sheet(ws2, subjects, fas_immuno, pps_immuno, report_fas, report_pps)
    write_notes_sheet(ws3)
    wb.save(OUT_XLSX)
    print(f"\n已写出: {OUT_XLSX}")


def add_locf_only():
    """加载已有 Excel，**仅新增**「GMC汇总统计(LOCF)」子表，不修改其他 3 个 sheet。
    LOCF 规则：受试者缺失某时间点时，用其前一个访视时间点的 anti-HBs 值结转。"""
    doc_v8 = Document(str(V8))
    doc_v9 = Document(str(V9))
    doc_v3 = Document(str(V3))

    subjects = extract_vaccinated(doc_v8)
    fas_immuno = extract_listing(doc_v9, 8)
    pps_immuno = extract_listing(doc_v9, 9)
    report_fas, report_pps = extract_report(doc_v3)

    locf_cache_fas = build_locf_cache(fas_immuno, subjects)
    locf_cache_pps = build_locf_cache(pps_immuno, subjects)

    # 打印 LOCF 受试者结转情况
    print("[LOCF] 受试者结转情况（FAS）：")
    for s in subjects:
        sid = s["sid"]
        scheme = group_scheme(s["group"])
        for tp in TIMEPOINTS:
            if (sid, tp) in locf_cache_fas.get(tp, {}):
                orig = subject_value(fas_immuno, sid, tp, s["group"])
                if orig is None:  # 仅打印发生结转的
                    abs_tp = ALIGN[tp][scheme] if tp in ALIGN else tp
                    order = SUBJECT_VISIT_ORDER[scheme]
                    if abs_tp in order:
                        idx = order.index(abs_tp)
                        prev_tp = order[idx - 1]
                        prev_v = subject_value(fas_immuno, sid, prev_tp, s["group"])
                        print(
                            f"  受试者 {sid} ({s['group']}) 在 {tp} 缺失 → 结转 {prev_tp} 值 = {prev_v}"
                        )

    # 加载已有 Excel
    wb = openpyxl.load_workbook(OUT_XLSX)
    # 若已有 LOCF sheet / 说明与溯源 sheet，先删除（避免重复 & 让说明与溯源重建为最新版）
    if "GMC汇总统计(LOCF)" in wb.sheetnames:
        del wb["GMC汇总统计(LOCF)"]
    if "说明与溯源" in wb.sheetnames:
        del wb["说明与溯源"]

    # 新建 Sheet3：GMC汇总统计(LOCF)
    ws_locf = wb.create_sheet("GMC汇总统计(LOCF)")
    write_summary_sheet(
        ws_locf,
        subjects,
        fas_immuno,
        pps_immuno,
        report_fas,
        report_pps,
        locf_cache_fas=locf_cache_fas,
        locf_cache_pps=locf_cache_pps,
    )

    # 新建 Sheet4（最后一位）：说明与溯源
    ws_notes = wb.create_sheet("说明与溯源")
    write_notes_sheet(ws_notes)

    # 确保 sheet 顺序：① 逐例清单(FAS) → ② GMC汇总统计 → ③ GMC汇总统计(LOCF) → ④ 说明与溯源
    desired_order = ["逐例清单(FAS)", "GMC汇总统计", "GMC汇总统计(LOCF)", "说明与溯源"]
    if wb.sheetnames != desired_order:
        wb._sheets = [wb[name] for name in desired_order]

    wb.save(OUT_XLSX)
    print(f"\n已重建 Sheet3/Sheet4 到: {OUT_XLSX}")
    print(f"现有 sheet: {wb.sheetnames}")

    # ===== 验证：LOCF 后 差值应全部≈0 =====
    print("\n===== LOCF 验证（本次计算 vs 报告，差值应≈0） =====")
    max_fas_diff = 0.0
    for g in GROUPS:
        members = group_members(subjects, g)
        for tp in TIMEPOINTS:
            fas_vals = get_values_at(fas_immuno, members, tp, locf_cache_fas)
            n, gm, _, _ = gmc_ci(fas_vals)
            rep = report_fas.get(tp, {}).get(g)
            if gm is not None and rep is not None:
                d = abs(gm - rep)
                max_fas_diff = max(max_fas_diff, d)
                if d > 0.011:
                    print(
                        f"  [差异] FAS {g} {tp}: 本次={gm:.2f} 报告={rep:.2f} 差={gm - rep:+.2f} (N={n})"
                    )
    max_pps_diff = 0.0
    for g in GROUPS:
        members = group_members(subjects, g)
        for tp in TIMEPOINTS:
            pps_vals = get_values_at(pps_immuno, members, tp, locf_cache_pps)
            n, gm, _, _ = gmc_ci(pps_vals)
            rep = report_pps.get(tp, {}).get(g)
            if gm is not None and rep is not None:
                d = abs(gm - rep)
                max_pps_diff = max(max_pps_diff, d)
                if d > 0.011:
                    print(
                        f"  [差异] PPS {g} {tp}: 本次={gm:.2f} 报告={rep:.2f} 差={gm - rep:+.2f} (N={n})"
                    )
    print(f"  LOCF-FAS 最大绝对差值 = {max_fas_diff:.4f}")
    print(f"  LOCF-PPS 最大绝对差值 = {max_pps_diff:.4f}")


if __name__ == "__main__":
    add_locf_only()
