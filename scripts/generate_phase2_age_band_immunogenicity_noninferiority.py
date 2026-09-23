"""
二期临床试验免疫原性（抗-HBs 阳转率）年龄层可比性非劣效分析
研究：YDSWX(TVAX-009)-002 —— 远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG 和铝佐剂）II 期基础阶段

数据源：review_materials/TFL-Phase2/第9册(清单2) 表16.2.6.2 基础阶段免疫原性清单(PPS)
统计方法：依 II 期 SAP V1.0
    - 单组率 95%CI：Clopper-Pearson
    - 组间率差 95%CI：Miettinen-Nurminen
    - 组间检验：Fisher 确切概率法 / 卡方
非劣效界值：-5%（率差 95%CI 下限 > -5% 判定成立）

比较口径：
    A 组（年龄层之间，试验组内部）-> 同一日历时点 M2 / M3（第二剂免后 1、2 个月）
    B 组（同一年龄层内，试验组 vs 对照组）-> 全免后 1 个月 / 全免后 2 个月
试验组仅保留高剂量：01 程序 = A2（0,1 月高剂量）；02 程序 = B2（0,2 月高剂量）
"""

import glob
import math
import os
from math import comb, erf, lgamma, log, sqrt

import docx
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ----------------------------------------------------------------------------
# 路径
# ----------------------------------------------------------------------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TFL_DIR = os.path.join(BASE, "review_materials", "TFL-Phase2")
OUT_DIR = os.path.join(BASE, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_XLSX = os.path.join(
    OUT_DIR, "TVAX-009-002(II)二期_免疫原性阳转率_年龄层可比性非劣效分析_PPS.xlsx"
)

# ----------------------------------------------------------------------------
# 统计函数
# ----------------------------------------------------------------------------


def betacf(a, b, x):
    """连分数展开（Numerical Recipes）"""
    MAXIT, EPS, FPMIN = 500, 3.0e-16, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betainc(a, b, x):
    """正则化不完全 Beta 函数 I_x(a,b)"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = lgamma(a + b) - lgamma(a) - lgamma(b) + a * log(x) + b * log(1.0 - x)
    bt = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def beta_ppf(q, a, b):
    """Beta 分布分位数（二分法）"""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson(x, n, alpha=0.05):
    """单组率 95%CI（Clopper-Pearson），返回百分数 (lo, hi, pct)"""
    p = 100.0 * x / n
    lo = 0.0 if x == 0 else 100.0 * beta_ppf(alpha / 2.0, x, n - x + 1)
    hi = 100.0 if x == n else 100.0 * beta_ppf(1.0 - alpha / 2.0, x + 1, n - x)
    return lo, hi, p


def norm_cdf(z):
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def norm_ppf(q):
    lo, hi = -40.0, 40.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _loglik(p, x1, n1, x2, n2, d):
    p1, p2 = p + d, p
    if not (1e-12 < p1 < 1 - 1e-12) or not (1e-12 < p2 < 1 - 1e-12):
        return -1e18
    ll = 0.0
    if x1 > 0:
        ll += x1 * log(p1)
    if n1 - x1 > 0:
        ll += (n1 - x1) * log(1.0 - p1)
    if x2 > 0:
        ll += x2 * log(p2)
    if n2 - x2 > 0:
        ll += (n2 - x2) * log(1.0 - p2)
    return ll


def _constrained_mle(x1, n1, x2, n2, d):
    """在 p1 - p2 = d 约束下的约束 MLE（黄金分割最大化）"""
    lo = max(1e-12, -d + 1e-12)
    hi = min(1.0 - 1e-12, 1.0 - d - 1e-12)
    if lo >= hi:
        return None
    gr = (sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c = b - gr * (b - a)
    e = a + gr * (b - a)
    fc = _loglik(c, x1, n1, x2, n2, d)
    fe = _loglik(e, x1, n1, x2, n2, d)
    for _ in range(300):
        if fc > fe:
            b, e, fe = e, c, fc
            c = b - gr * (b - a)
            fc = _loglik(c, x1, n1, x2, n2, d)
        else:
            a, c, fc = c, e, fe
            e = a + gr * (b - a)
            fe = _loglik(e, x1, n1, x2, n2, d)
        if abs(b - a) < 1e-13:
            break
    return (a + b) / 2.0


def mn_z(x1, n1, x2, n2, d, correct=True):
    """Miettinen-Nurminen 分数统计量 Z(d)"""
    p1h, p2h = x1 / n1, x2 / n2
    p = _constrained_mle(x1, n1, x2, n2, d)
    if p is None:
        return None
    p1t, p2t = p + d, p
    var = p1t * (1.0 - p1t) / n1 + p2t * (1.0 - p2t) / n2
    if correct:
        var *= (n1 + n2) / (n1 + n2 - 1.0)
    if var <= 0:
        return None
    return (p1h - p2h - d) / sqrt(var)


def mn_ci(x1, n1, x2, n2, alpha=0.05, correct=True):
    """Miettinen-Nurminen 率差 95%CI，返回百分数 (diff, lo, hi)"""
    z = norm_ppf(1.0 - alpha / 2.0)
    d_hat = 100.0 * (x1 / n1 - x2 / n2)

    def solve(target):
        lo, hi = -0.999999, 0.999999
        for _ in range(200):
            mid = (lo + hi) / 2.0
            v = mn_z(x1, n1, x2, n2, mid, correct)
            if v is None:
                return None
            if v > target:
                lo = mid
            else:
                hi = mid
            if hi - lo < 1e-12:
                break
        return 100.0 * (lo + hi) / 2.0

    return d_hat, solve(z), solve(-z)


def fisher_exact_2x2(a, b, c, d):
    """2x2 双侧 Fisher 确切概率法 P 值"""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def pr(x):
        if x < 0 or x > r1 or c1 - x < 0 or c1 - x > n - r1:
            return 0.0
        return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)

    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    p_obs = pr(a)
    if p_obs <= 0:
        return 1.0
    tol = p_obs * (1.0 + 1e-9)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= tol))


# ----------------------------------------------------------------------------
# 自检：与 TFL 官方数字校准
# ----------------------------------------------------------------------------
def self_check():
    print("=" * 78)
    print("统计函数自检（对照 TFL-Phase2 官方数字）")
    print("=" * 78)
    ok = True

    # Clopper-Pearson：C3 首剂免后2个月 64/74 -> (76.55, 93.32)
    lo, hi, p = clopper_pearson(64, 74)
    t = abs(lo - 76.55) < 0.02 and abs(hi - 93.32) < 0.02
    ok &= t
    print(f"  [Clopper-Pearson] C3 M2 64/74 = {p:.2f}%  CI({lo:.2f}, {hi:.2f})  官方(76.55, 93.32)  {'PASS' if t else 'FAIL'}")

    # Clopper-Pearson：A2 首剂免后2个月 140/143 -> (93.99, 99.57)
    lo, hi, p = clopper_pearson(140, 143)
    t = abs(lo - 93.99) < 0.02 and abs(hi - 99.57) < 0.02
    ok &= t
    print(f"  [Clopper-Pearson] A2 M2 140/143 = {p:.2f}%  CI({lo:.2f}, {hi:.2f})  官方(93.99, 99.57)  {'PASS' if t else 'FAIL'}")

    # Miettinen-Nurminen：C3 vs C2 M2 (64/74 vs 23/73) -> 54.98 (40.55, 66.85)
    d, lo, hi = mn_ci(64, 74, 23, 73)
    t = abs(d - 54.98) < 0.02 and abs(lo - 40.55) < 0.05 and abs(hi - 66.85) < 0.05
    ok &= t
    print(f"  [Miettinen-Nurminen] C3 vs C2 M2 = {d:.2f}%  CI({lo:.2f}, {hi:.2f})  官方 54.98 (40.55, 66.85)  {'PASS' if t else 'FAIL'}")

    # Miettinen-Nurminen：A1 vs C1 M2 (136/144 vs 94/144) -> 29.17 (20.58, 37.90)
    d, lo, hi = mn_ci(136, 144, 94, 144)
    t = abs(d - 29.17) < 0.02 and abs(lo - 20.58) < 0.05 and abs(hi - 37.90) < 0.05
    ok &= t
    print(f"  [Miettinen-Nurminen] A1 vs C1 M2 = {d:.2f}%  CI({lo:.2f}, {hi:.2f})  官方 29.17 (20.58, 37.90)  {'PASS' if t else 'FAIL'}")

    print(f"  ==> 自检{'全部通过' if ok else '存在偏差'}")
    print()
    return ok


# ----------------------------------------------------------------------------
# 数据提取
# ----------------------------------------------------------------------------
VIS_FULL = {
    # 组别标签 -> (全免后1个月访视, 全免后2个月访视)
    "A2": ("首剂接种后2个月", "首剂接种后3个月"),
    "B2": ("首剂接种后3个月", "首剂接种后4个月"),
    "C1": ("首剂接种后7个月", "首剂接种后8个月"),
}

GROUP_NAME = {
    "A2": "0,1月高剂量组(A2)",
    "B2": "0,2月高剂量组(B2)",
    "C1": "阳性对照组(C1)",
    "C3": "0,1,6月高剂量组(C3)",
}


def age_band(a):
    if 50 <= a <= 54:
        return "50-54"
    if 55 <= a <= 59:
        return "55-59"
    if 60 <= a <= 65:
        return "60-65"
    return None


def load_pps_records():
    path = glob.glob(os.path.join(TFL_DIR, "*清单2*.docx"))[0]
    d = docx.Document(path)
    t = d.tables[9]  # 表16.2.6.2 基础阶段免疫原性清单(PPS)
    recs = []
    for r in t.rows[1:]:
        cells = [c.text.strip().replace("\n", "") for c in r.cells]
        try:
            age = int(cells[4])
        except ValueError:
            continue
        # 阳转(4倍增长)：免前阴性者阳转 或 免前阳性者4倍增长
        event = (cells[9] == "是") or (cells[10] == "是")
        recs.append(
            dict(grp=cells[1], vis=cells[5], age=age, sid=cells[2], event=event)
        )
    return recs


def subset(recs, groups, band, visit):
    """按组别集合 / 年龄层 / 访视 取子集；band 可为 '50-59' 合并标记"""
    out = []
    for r in recs:
        if r["grp"] not in groups:
            continue
        if band == "50-59":
            b = age_band(r["age"])
            if b not in ("50-54", "55-59"):
                continue
        elif age_band(r["age"]) != band:
            continue
        if r["vis"] != visit:
            continue
        out.append(r)
    return out


def count(sub):
    return sum(1 for r in sub if r["event"]), len(sub)


# ----------------------------------------------------------------------------
# 比较计算
# ----------------------------------------------------------------------------


def make_row(label, subj, ref, margin=-5.0):
    """subj/ref 均为 (x, n)；返回一行结果字典"""
    x1, n1 = subj
    x2, n2 = ref
    lo1, hi1, p1 = clopper_pearson(x1, n1)
    lo2, hi2, p2 = clopper_pearson(x2, n2)
    diff, dlo, dhi = mn_ci(x1, n1, x2, n2)
    pv = fisher_exact_2x2(x1, n1 - x1, x2, n2 - x2)
    # 非劣效：率差 95%CI 下限 > 界值
    if dlo is None:
        verdict = "无法计算"
    elif dlo > margin:
        verdict = "成立（非劣效）"
    else:
        verdict = "不成立"
    return dict(
        tp=label,
        n1=n1, x1=x1, p1=p1, lo1=lo1, hi1=hi1,
        n2=n2, x2=x2, p2=p2, lo2=lo2, hi2=hi2,
        diff=diff, dlo=dlo, dhi=dhi, p=pv,
        margin=margin, verdict=verdict,
    )


def build_comparisons(recs):
    """返回 [(sheet_name, meta, [rows])]"""
    out = []

    # ---------- A 组：年龄层之间，同一日历时点 M2 / M3 ----------
    A_SPEC = [
        ("A1_60-65vs55-59", "60~65 岁 vs 55~59 岁",
         ("C3", "60-65"), ("A2", "55-59"),
         "年龄层间可比性：60~65 岁（0,1,6月高剂量，M2/M3 时仅完成前 2 剂）vs 55~59 岁（0,1月高剂量）"),
        ("A2_55-59vs50-54", "55~59 岁 vs 50~54 岁",
         ("A2", "55-59"), ("A2", "50-54"),
         "年龄层间可比性：55~59 岁 vs 50~54 岁（均为 0,1月高剂量组 A2）"),
        ("A3_60-65vs50-59", "60~65 岁 vs 50~59 岁（合并）",
         ("C3", "60-65"), ("A2", "50-59"),
         "年龄层间可比性：60~65 岁（0,1,6月高剂量，M2/M3 时仅完成前 2 剂）vs 50~59 岁合并（0,1月高剂量）"),
    ]
    for sheet, title, (g1, b1), (g2, b2), desc in A_SPEC:
        rows = []
        for vis, tp in [("首剂接种后2个月", "M2（第二剂免后1个月）"),
                        ("首剂接种后3个月", "M3（第二剂免后2个月）")]:
            s = count(subset(recs, [GROUP_NAME[g1]], b1, vis))
            r = count(subset(recs, [GROUP_NAME[g2]], b2, vis))
            rows.append(make_row(tp, s, r))
        out.append((sheet, dict(title=title, desc=desc, kind="A",
                                arm1=f"{GROUP_NAME[g1]} · {b1} 岁",
                                arm2=f"{GROUP_NAME[g2]} · {b2} 岁",
                                basis="同一日历时点（M2 / M3，即第二剂免后 1、2 个月）"),
                    rows))

    # ---------- B 组：同一年龄层，试验组 vs 对照组（全免后 1 / 2 个月）----------
    B_SPEC = []
    idx = 1
    for band in ["50-54", "55-59", "50-59"]:
        for prog, grp in [("01", "A2"), ("02", "B2")]:
            B_SPEC.append((
                f"B{idx}_{band}岁_{prog}程序",
                f"{band} 岁 · {prog}程序",
                grp, band,
                f"同一年龄层内比较：{band} 岁 · {prog}程序高剂量试验疫苗（{GROUP_NAME[grp]}）vs 阳性对照疫苗（{GROUP_NAME['C1']}），基于全免后 1、2 个月",
            ))
            idx += 1

    for sheet, title, grp, band, desc in B_SPEC:
        rows = []
        v1, v2 = VIS_FULL[grp]
        w1, w2 = VIS_FULL["C1"]
        rows.append(make_row(f"全免后1个月（试验 {v1.replace('首剂接种后','M').replace('个月','')} / 对照 {w1.replace('首剂接种后','M').replace('个月','')}）",
                             count(subset(recs, [GROUP_NAME[grp]], band, v1)),
                             count(subset(recs, [GROUP_NAME["C1"]], band, w1))))
        rows.append(make_row(f"全免后2个月（试验 {v2.replace('首剂接种后','M').replace('个月','')} / 对照 {w2.replace('首剂接种后','M').replace('个月','')}）",
                             count(subset(recs, [GROUP_NAME[grp]], band, v2)),
                             count(subset(recs, [GROUP_NAME["C1"]], band, w2))))
        out.append((sheet, dict(title=title, desc=desc, kind="B",
                                arm1=f"{GROUP_NAME[grp]} · {band} 岁（试验组）",
                                arm2=f"{GROUP_NAME['C1']} · {band} 岁（对照组）",
                                basis="全免后 1 个月 / 全免后 2 个月"),
                    rows))
    return out


# ----------------------------------------------------------------------------
# Excel 输出
# ----------------------------------------------------------------------------
TITLE_FONT = Font(name="微软雅黑", size=14, bold=True, color="1F3864")
SUB_FONT = Font(name="微软雅黑", size=10, color="404040")
HDR_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10)
BOLD_FONT = Font(name="微软雅黑", size=10, bold=True)
HDR_FILL = PatternFill("solid", fgColor="2F5597")
SUBHDR_FILL = PatternFill("solid", fgColor="D9E2F3")
OK_FILL = PatternFill("solid", fgColor="C6EFCE")
NG_FILL = PatternFill("solid", fgColor="FFC7CE")
WARN_FILL = PatternFill("solid", fgColor="FFEB9C")
THIN = Side(style="thin", color="B4C6E7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_header(ws, row, ncol, fill=HDR_FILL, font=HDR_FONT):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = font
        cell.fill = fill
        cell.alignment = CENTER
        cell.border = BORDER


def write_comp_sheet(ws, sheet_name, meta, rows):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 30
    for col in "BCDEFGHIJKL":
        ws.column_dimensions[col].width = 14
    ws.column_dimensions["L"].width = 16
    ws.column_dimensions["M"].width = 14

    ws["A1"] = f"{sheet_name.split('_', 1)[0]}｜{meta['title']}"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:M1")
    ws.row_dimensions[1].height = 26

    ws["A2"] = f"分析人群：PPS　|　指标：抗-HBs 阳转率　|　比较口径：{meta['basis']}　|　非劣效界值：−5%"
    ws["A2"].font = SUB_FONT
    ws.merge_cells("A2:M2")

    ws["A3"] = meta["desc"]
    ws["A3"].font = SUB_FONT
    ws["A3"].alignment = WRAP
    ws.merge_cells("A3:M3")
    ws.row_dimensions[3].height = 30

    ws["A5"] = f"受试组：{meta['arm1']}"
    ws["A6"] = f"参照组：{meta['arm2']}"
    ws["A5"].font = BOLD_FONT
    ws["A6"].font = BOLD_FONT
    ws.merge_cells("A5:M5")
    ws.merge_cells("A6:M6")

    # 表头
    hdr = ["时间点",
           "受试组 n/N", "阳转率(%)", "95%CI下限", "95%CI上限",
           "参照组 n/N", "阳转率(%)", "95%CI下限", "95%CI上限",
           "率差(%)", "95%CI下限", "95%CI上限", "非劣效判定"]
    r0 = 8
    for i, h in enumerate(hdr, start=1):
        ws.cell(row=r0, column=i, value=h)
    style_header(ws, r0, len(hdr))

    # 第二层分组表头
    grp = ["", "受试组（拟证明非劣）", "", "", "", "参照组", "", "", "", "组间比较", "", "", ""]
    for i, h in enumerate(grp, start=1):
        ws.cell(row=r0 - 1, column=i, value=h)
    style_header(ws, r0 - 1, len(grp), fill=SUBHDR_FILL,
                 font=Font(name="微软雅黑", size=10, bold=True, color="1F3864"))
    ws.merge_cells(start_row=r0 - 1, start_column=2, end_row=r0 - 1, end_column=5)
    ws.merge_cells(start_row=r0 - 1, start_column=6, end_row=r0 - 1, end_column=9)
    ws.merge_cells(start_row=r0 - 1, start_column=10, end_row=r0 - 1, end_column=12)

    r = r0 + 1
    for row in rows:
        vals = [
            row["tp"],
            f"{row['x1']}/{row['n1']}", round(row["p1"], 2),
            round(row["lo1"], 2), round(row["hi1"], 2),
            f"{row['x2']}/{row['n2']}", round(row["p2"], 2),
            round(row["lo2"], 2), round(row["hi2"], 2),
            round(row["diff"], 2), round(row["dlo"], 2), round(row["dhi"], 2),
            row["verdict"],
        ]
        for i, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=i, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = CENTER if i > 1 else WRAP
        ws.cell(row=r, column=13).fill = OK_FILL if row["verdict"].startswith("成立") else NG_FILL
        ws.cell(row=r, column=13).font = BOLD_FONT
        ws.row_dimensions[r].height = 32
        r += 1

    # 判定说明
    r += 1
    ws.cell(row=r, column=1, value="判定规则：").font = BOLD_FONT
    ws.cell(row=r, column=2,
            value="率差（受试组 − 参照组）的 95%CI 下限 > −5%，判定非劣效成立；否则为不成立（不成立仅表示未能确认非劣效，不等同于劣效）。")
    ws.cell(row=r, column=2).font = SUB_FONT
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=13)
    ws.cell(row=r, column=2).alignment = WRAP
    ws.row_dimensions[r].height = 30

    ws.freeze_panes = "A9"


def write_summary(ws, comps):
    ws.sheet_view.showGridLines = False
    widths = [10, 26, 26, 24, 10, 10, 10, 10, 10, 10, 10, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws["A1"] = "非劣效判定汇总（PPS｜抗-HBs 阳转率｜界值 −5%）"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:L1")
    ws.row_dimensions[1].height = 26

    hdr = ["编号", "比较", "受试组", "参照组", "时间点",
           "受试组 n/N", "受试组率(%)", "参照组 n/N", "参照组率(%)",
           "率差(%)", "95%CI下限", "非劣效判定"]
    for i, h in enumerate(hdr, start=1):
        ws.cell(row=3, column=i, value=h)
    style_header(ws, 3, len(hdr))

    r = 4
    for sheet, meta, rows in comps:
        code = sheet.split("_", 1)[0]
        for row in rows:
            vals = [code, meta["title"], meta["arm1"], meta["arm2"], row["tp"],
                    f"{row['x1']}/{row['n1']}", round(row["p1"], 2),
                    f"{row['x2']}/{row['n2']}", round(row["p2"], 2),
                    round(row["diff"], 2), round(row["dlo"], 2), row["verdict"]]
            for i, v in enumerate(vals, start=1):
                cell = ws.cell(row=r, column=i, value=v)
                cell.font = BODY_FONT
                cell.border = BORDER
                cell.alignment = CENTER if i != 2 else WRAP
            ws.cell(row=r, column=12).fill = OK_FILL if row["verdict"].startswith("成立") else NG_FILL
            ws.cell(row=r, column=12).font = BOLD_FONT
            ws.row_dimensions[r].height = 30
            r += 1
    ws.freeze_panes = "A4"


def build_conclusion_text(comps):
    """由计算结果动态生成说明页结论"""
    idx = {(s.split("_", 1)[0]): (m, r) for s, m, r in comps}
    lines = []

    def fmt(code, k):
        m, rows = idx[code]
        row = rows[k]
        return (f"{row['x1']}/{row['n1']}（{row['p1']:.2f}%）vs "
                f"{row['x2']}/{row['n2']}（{row['p2']:.2f}%），"
                f"率差 {row['diff']:.2f}%，95%CI（{row['dlo']:.2f}, {row['dhi']:.2f}），"
                f"判定：{row['verdict']}")

    lines.append("【六、各年龄层阳转率可比性结论】")
    lines.append("（以下时点为 M2＝首剂接种后 2 个月＝第二剂免后 1 个月；M3＝首剂接种后 3 个月＝第二剂免后 2 个月）")
    lines.append("")
    lines.append("1）60~65 岁 vs 55~59 岁（A1，01 程序高剂量口径）")
    lines.append("   M2：" + fmt("A1", 0))
    lines.append("   M3：" + fmt("A1", 1))
    a1 = idx["A1"][1]
    n_ok = sum(1 for x in a1 if x["verdict"].startswith("成立"))
    lines.append(f"   小结：{'两个时点均达到非劣效' if n_ok == 2 else ('仅部分时点达到非劣效' if n_ok == 1 else '两个时点均未达到非劣效')}。")
    lines.append("")
    lines.append("2）55~59 岁 vs 50~54 岁（A2，01 程序高剂量口径）")
    lines.append("   M2：" + fmt("A2", 0))
    lines.append("   M3：" + fmt("A2", 1))
    a2 = idx["A2"][1]
    n_ok = sum(1 for x in a2 if x["verdict"].startswith("成立"))
    lines.append(f"   小结：{'两个时点均达到非劣效' if n_ok == 2 else ('仅部分时点达到非劣效' if n_ok == 1 else '两个时点均未达到非劣效')}。")
    lines.append("")
    lines.append("3）60~65 岁 vs 50~59 岁（合并）（A3，最终目的）")
    lines.append("   M2：" + fmt("A3", 0))
    lines.append("   M3：" + fmt("A3", 1))
    a3 = idx["A3"][1]
    n_ok = sum(1 for x in a3 if x["verdict"].startswith("成立"))
    lines.append(f"   小结：{'两个时点均达到非劣效' if n_ok == 2 else ('仅部分时点达到非劣效' if n_ok == 1 else '两个时点均未达到非劣效')}。")
    lines.append("")

    lines.append("【七、同一年龄层内 试验组 vs 对照组（全免后 1、2 个月）】")
    lines.append("")
    for code in ["B1", "B2", "B3", "B4", "B5", "B6"]:
        m, rows = idx[code]
        lines.append(f"{code}｜{m['title']}")
        lines.append("   全免后1个月：" + fmt(code, 0))
        lines.append("   全免后2个月：" + fmt(code, 1))
    lines.append("")

    lines.append("【八、最终结论与依据】")
    lines.append("")
    a3rows = idx["A3"][1]
    ok_m2 = a3rows[0]["verdict"].startswith("成立")
    ok_m3 = a3rows[1]["verdict"].startswith("成立")
    m3 = a3rows[1]
    m2 = a3rows[0]
    if ok_m2 and ok_m3:
        concl = ("结论：在 PPS 人群、抗-HBs 阳转率终点上，60~65 岁人群在 M2、M3 两个时点均非劣于 50~59 岁人群"
                 "（率差 95%CI 下限均 > −5%），两年龄层免疫原性具有可比性。")
    elif ok_m3 or ok_m2:
        which = "M3（第二剂免后 2 个月）" if ok_m3 else "M2（第二剂免后 1 个月）"
        concl = (f"结论：60~65 岁人群在 {which} 时点非劣于 50~59 岁人群（率差 95%CI 下限 > −5%），"
                 f"另一时点未达到非劣效标准，故可比性仅在该时点得到确证，尚不足以在两个时点上全面确证。")
    else:
        concl = ("结论：在 PPS 人群、抗-HBs 阳转率终点上，60~65 岁人群在 M2、M3 两个时点的率差 95%CI 下限均未超过 −5%，"
                 "未能确证非劣效。即现有数据尚不足以支持【60~65 岁阳转率非劣于 50~59 岁】的结论。")
    lines.append("1）" + concl)
    lines.append("")
    lines.append("2）依据链：")
    lines.append("   ① 60~65 岁数据取自 C3 组（0,1,6 月高剂量）。C3 第 3 剂在首剂后 6 个月接种，"
                 "故其在 M2、M3 时点仅完成 0、1 月两剂，与 0,1 月程序（A2）的 M2、M3 在剂次数与时间点上完全等效，"
                 "因此两年龄层可在同一时点直接比较。")
    lines.append("   ② 50~59 岁为 50~54 岁与 55~59 岁的合并人群，与 60~65 岁构成年龄上的连续衔接。")
    lines.append("   ③ 试验组统一采用高剂量（A2 / B2 / C3 均为高剂量），排除剂量混杂。")
    lines.append("   ④ 统计方法依 II 期 SAP：单组率用 Clopper-Pearson 法，组间率差用 Miettinen-Nurminen 法，"
                 "非劣效界值统一取 −5%，以率差 95%CI 下限 > −5% 为判定标准。")
    lines.append("   ⑤ 计算所用阳转率与 TFL 表 16.2.6.2（PPS 免疫原性清单）完全一致，"
                 "并已用 TFL 官方数字逐项校准（Clopper-Pearson 与 Miettinen-Nurminen 均通过校验）。")
    lines.append("")
    lines.append("3）结果解读（重要，避免误读）：")
    lines.append(f"   ① 在 M3（第二剂免后 2 个月）时点，60~65 岁阳转率 {m3['p1']:.2f}%（{m3['x1']}/{m3['n1']}）"
                 f"与 50~59 岁 {m3['p2']:.2f}%（{m3['x2']}/{m3['n2']}）几乎相同，"
                 f"率差点估计为 {m3['diff']:+.2f}%，方向为正（60~65 岁略高于 50~59 岁）。"
                 f"该时点未获确证，源于各细分层样本量较小导致 95%CI 下限（{m3['dlo']:.2f}%）未能越过 −5%，"
                 f"并非观察到阳转率的实质性下降。")
    lines.append(f"   ② 在 M2（第二剂免后 1 个月）时点，率差点估计为 {m2['diff']:+.2f}%，"
                 f"95%CI（{m2['dlo']:.2f}, {m2['dhi']:.2f}）。需注意参照组 55~59 岁 01 程序在该时点阳转率为 100%（17/17），"
                 f"存在天花板效应，会系统性拉大负向率差并使区间变宽，解释时须谨慎。")
    lines.append("   ③ 综合判断：从点估计看，60~65 岁与 50~59 岁的阳转率数值高度接近，两年龄层免疫原性在数值上具有可比性；"
                 "但按预设的 −5% 界值与 95%CI 下限标准，本次数据未能在两个时点上获得统计学确证。"
                 "如需形成确证性结论，建议扩大高年龄层样本量，或在后续研究中预先设定该年龄分层与对应的检验策略。")
    lines.append("")

    lines.append("【九、局限性说明】")
    lines.append("")
    lines.append("1）样本量限制：本分析系在 II 期既有分层内按实际年龄二次筛选，各细分层样本量较小"
                 "（如 C1 对照组 50~54 岁仅 12 例、55~59 岁 22 例；A2 组 55~59 岁 17 例）。"
                 "样本量小会直接导致率差 95%CI 变宽，进而使非劣效难以成立；"
                 "此处【不成立】应理解为【未能确认非劣效】，不等同于证实劣效。")
    lines.append("2）天花板效应：02 程序（0,2 月高剂量 B2）在 50~54、55~59 岁各时点阳转率均达 100%，"
                 "同时 55~59 岁 01 程序亦为 100%。在率值触及 100% 时，Miettinen-Nurminen 法给出的区间会明显偏宽，"
                 "对结果的解释需谨慎。")
    lines.append("3）年龄层非预设分层：60~65 岁并非 II 期预设年龄分层，系按实际年龄从 ≥60 岁队列中筛选得到，"
                 "属事后探索性分析，结论的外推需谨慎。")
    lines.append("4）组间基线可比性：本分析仅针对阳转率单终点，未校正性别、基线抗体水平等潜在混杂因素；"
                 "各组基线抗-HBs 阳性率均接近 0，基线均衡性良好。")
    lines.append("5）分析人群：仅基于 PPS，未同时提供 FAS 结果。")
    return lines


def build_overview(comps):
    """说明页置顶的核心结论速览"""
    idx = {s.split("_", 1)[0]: (m, r) for s, m, r in comps}
    a1, a2, a3 = idx["A1"][1], idx["A2"][1], idx["A3"][1]
    b3, b4 = idx["B3"][1], idx["B4"][1]

    def one(row):
        return (f"{row['x1']}/{row['n1']}={row['p1']:.2f}% vs {row['x2']}/{row['n2']}={row['p2']:.2f}%，"
                f"率差 {row['diff']:+.2f}%，95%CI（{row['dlo']:.2f}, {row['dhi']:.2f}）→ {row['verdict']}")

    L = []
    L.append("【核心结论速览】（完整数据、推导过程与局限性见后文第一~九节）")
    L.append("")
    L.append("1）最终目的：60~65 岁 vs 50~59 岁（50~54 与 55~59 合并）")
    L.append("   M2（第二剂免后1个月）：" + one(a3[0]))
    L.append("   M3（第二剂免后2个月）：" + one(a3[1]))
    L.append("   要点：M3 时点两年龄层阳转率几乎相同（点估计方向为正），未获确证系各细分层样本量小、"
             "可信区间过宽所致，并非观察到阳转率下降。详见第八节【结果解读】。")
    L.append("")
    L.append("2）60~65 岁 vs 55~59 岁")
    L.append("   M2（第二剂免后1个月）：" + one(a1[0]))
    L.append("   M3（第二剂免后2个月）：" + one(a1[1]))
    L.append("   要点：参照组 55~59 岁 01 程序在两时点均为 100%（17/17），存在天花板效应，会拉大负向率差，解释须谨慎。")
    L.append("")
    L.append("3）55~59 岁 vs 50~54 岁")
    L.append("   M2（第二剂免后1个月）：" + one(a2[0]))
    L.append("   M3（第二剂免后2个月）：" + one(a2[1]))
    L.append("")
    L.append("4）55~59 岁 试验组 vs 对照组（全免后，本次重点关注）")
    L.append("   01程序 全免后1个月：" + one(b3[0]))
    L.append("   01程序 全免后2个月：" + one(b3[1]))
    L.append("   02程序 全免后1个月：" + one(b4[0]))
    L.append("   02程序 全免后2个月：" + one(b4[1]))
    L.append("   要点：四个比较的率差点估计均为正向或为 0（+4.55%、0.00%、+4.55%、0.00%），"
             "试验组数值不低于对照组；未获确证同样受限于对照组在该年龄层样本量小（22 例）。")
    L.append("")
    return L


def write_notes(ws, comps):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 118

    ws["A1"] = "Ⅱ期免疫原性（抗-HBs 阳转率）年龄层可比性非劣效分析 —— 说明页"
    ws["A1"].font = Font(name="微软雅黑", size=15, bold=True, color="1F3864")
    ws.row_dimensions[1].height = 30

    top = [
        "【一、分析目的】",
        "评估 YDSWX(TVAX-009)-002（远大赛威信重组乙型肝炎疫苗〔汉逊酵母，CpG 和铝佐剂〕Ⅱ期基础阶段）中，"
        "50~54 岁、55~59 岁、50~59 岁（合并）与 60~65 岁各年龄层接种试验疫苗（高剂量）后抗-HBs 阳转率的可比性，"
        "重点确证 60~65 岁人群阳转率是否非劣于 50~59 岁人群；并在同一年龄层内比较 01 / 02 程序试验疫苗与阳性对照疫苗"
        "在全免后 1、2 个月的阳转率。",
        "",
        "【二、数据来源】",
        "数据源：review_materials/TFL-Phase2/《YDSWX(TVAX-009)-002(Ⅱ)-基础阶段-统计分析报告-第9册(清单2)》"
        "表 16.2.6.2 基础阶段免疫原性清单（PPS），个体级记录，含研究编号、年龄、组别、访视、抗-HBs 浓度、"
        "是否抗-HBs 阳转、是否抗-HBs 4 倍增长。",
        "统计方法依据：《远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG 和铝佐剂）Ⅱ期-SAP-V1.0》。",
        "制表逻辑参照：《第2册(免疫原性1)》《第3册(免疫原性2)》相应时点阳转率表。",
        "",
        "【三、关键定义】",
        "1）分析人群：PPS（各时点对应的 PPS 集合，直接采用清单中该时点的在集记录）。",
        "2）终点指标：抗-HBs 阳转率。定义为免前抗-HBs 浓度 <10 mIU/ml 者，免后相应时间点抗-HBs 浓度 ≥10 mIU/ml 的受试者百分比；"
        "免前 ≥10 mIU/ml 者以免后 4 倍及以上增长计（与 TFL 中【抗-HBs 阳转（4 倍增长）率】口径一致）。",
        "3）试验组（仅高剂量）：01 程序 = A2 组（0,1 月高剂量）；02 程序 = B2 组（0,2 月高剂量）；"
        "60~65 岁 = C3 组（0,1,6 月高剂量，≥60 岁队列）中实际年龄 60~65 岁者。低剂量组（A1/B1）不纳入。",
        "4）对照组：C1 组（阳性对照，0,1,6 月程序，18-59 岁队列）。",
        "5）50~59 岁 = 50~54 岁与 55~59 岁合并；60~65 岁按实际年龄从 ≥60 岁队列筛选。",
        "",
        "【四、时点口径（两类比较分别采用不同口径）】",
        "① 年龄层之间的比较（A 组）→ 采用同一日历时点 M2、M3：",
        "   M2 = 首剂接种后 2 个月 = 第二剂免后 1 个月；M3 = 首剂接种后 3 个月 = 第二剂免后 2 个月。",
        "   说明：C3 组第 3 剂在首剂后 6 个月接种，故 C3 在 M2、M3 时点仅完成 0、1 月两剂，"
        "与 0,1 月程序（A2）的 M2、M3 在剂次数与时间点上完全等效，可比性成立。",
        "   若改用【全免后】，则 C3 全免后落在 M7/M8，而 A2 全免后落在 M2/M3，两者相差 5 个月，不具备可比性，故年龄层间比较不采用全免后口径。",
        "② 同一年龄层内 试验组 vs 对照组（B 组）→ 采用全免后 1 个月、全免后 2 个月：",
        "   A2（2 剂 0,1 月）：全免后 1 个月 = M2，全免后 2 个月 = M3；",
        "   B2（2 剂 0,2 月）：全免后 1 个月 = M3，全免后 2 个月 = M4；",
        "   C1（3 剂 0,1,6 月）：全免后 1 个月 = M7，全免后 2 个月 = M8。",
        "",
        "【五、统计方法与非劣效判定规则】",
        "1）单组阳转率 95% 可信区间：Clopper-Pearson 法。",
        "2）组间率差及其 95% 可信区间：Miettinen-Nurminen 法（含 (n1+n2)/(n1+n2−1) 小样本校正）。",
        "3）组间差异检验：卡方检验 / Fisher 确切概率法。",
        "4）非劣效界值：−5%（与既有分析保持一致）。",
        "5）判定规则：率差（受试组 − 参照组）的 95%CI 下限 > −5%，判定非劣效成立；否则判定不成立。",
        "   【不成立】仅表示现有数据未能确认非劣效，并不等同于证实劣效。",
        "6）数值修约：率、率差及可信区间均保留至小数点后 2 位（依 SAP 规定）。",
        "",
    ]
    body = build_overview(comps) + top + build_conclusion_text(comps)

    r = 3
    for line in body:
        cell = ws.cell(row=r, column=1, value=line)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if line.startswith("【"):
            cell.font = Font(name="微软雅黑", size=11, bold=True, color="1F3864")
        else:
            cell.font = Font(name="微软雅黑", size=10)
        est = max(1, min(8, (len(line) // 55) + (1 if len(line) % 55 else 0) + 1))
        ws.row_dimensions[r].height = 16 * est if line else 8
        r += 1


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
def main():
    self_check()
    recs = load_pps_records()
    print(f"PPS 免疫原性清单记录数：{len(recs)}")

    comps = build_comparisons(recs)

    wb = Workbook()
    ws_notes = wb.active
    ws_notes.title = "00_说明"
    write_notes(ws_notes, comps)

    ws_sum = wb.create_sheet("01_汇总")
    write_summary(ws_sum, comps)

    for sheet, meta, rows in comps:
        ws = wb.create_sheet(sheet[:31])
        write_comp_sheet(ws, sheet, meta, rows)

    wb.save(OUT_XLSX)
    print(f"\n已生成：{OUT_XLSX}")

    print("\n" + "=" * 78)
    print("结果概览")
    print("=" * 78)
    for sheet, meta, rows in comps:
        print(f"\n{sheet}｜{meta['title']}")
        for row in rows:
            print(f"   {row['tp']:<42s} "
                  f"{row['x1']}/{row['n1']}={row['p1']:6.2f}%  vs  "
                  f"{row['x2']}/{row['n2']}={row['p2']:6.2f}%  "
                  f"率差 {row['diff']:7.2f}%  CI({row['dlo']:7.2f}, {row['dhi']:6.2f})  "
                  f"→ {row['verdict']}")


if __name__ == "__main__":
    main()
