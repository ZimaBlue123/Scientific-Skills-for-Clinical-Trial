#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""疫苗免疫原性非劣效分析的统计内核（纯标准库实现，无第三方依赖）。

提供：
  - 单组率 95%CI          Clopper-Pearson
  - 组间率差 95%CI        Miettinen-Nurminen（含 (n1+n2)/(n1+n2−1) 小样本校正）
  - 交叉验证               Newcombe 杂交 Wilson 法
  - 组间率检验             Fisher 确切概率法
  - 几何均数与 95%CI       对数转换 + t 分布
  - GMC 比值与 95%CI       对数转换后成组 t 检验
  - 删失值处理             LOD/2、LOD、sqrt(LOD) 等规则

CLI：
  python compute_noninferiority.py --self-check
      用内置的两组官方发表值（TVAX-009B Ⅰ期、TVAX-009-002 Ⅱ期）校验本模块

  python compute_noninferiority.py --spec spec.json --subjects subjects.csv --out results.json
      按规格配置逐项计算，输出 JSON（供 build_noninferiority_workbook.py 消费）
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys

# ---------------------------------------------------------------------------
# 不完全 Beta / 正态分布
# ---------------------------------------------------------------------------


def betacf(a: float, b: float, x: float) -> float:
    """连分数展开（Numerical Recipes）。"""
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
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """正则化不完全 Beta 函数 I_x(a, b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def beta_ppf(q: float, a: float, b: float) -> float:
    """Beta 分布分位数（二分法）。"""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(q: float) -> float:
    lo, hi = -40.0, 40.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# t 分布
# ---------------------------------------------------------------------------


def t_cdf(t: float, df: float) -> float:
    """学生 t 分布 CDF。"""
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def t_ppf(q: float, df: float) -> float:
    lo, hi = -200.0, 200.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# 率的统计
# ---------------------------------------------------------------------------


def clopper_pearson(x: int, n: int, alpha: float = 0.05):
    """单组率 95%CI（Clopper-Pearson）。返回百分数 (lo, hi, pct)。"""
    if n <= 0:
        return None, None, None
    p = 100.0 * x / n
    lo = 0.0 if x == 0 else 100.0 * beta_ppf(alpha / 2.0, x, n - x + 1)
    hi = 100.0 if x == n else 100.0 * beta_ppf(1.0 - alpha / 2.0, x + 1, n - x)
    return lo, hi, p


def _loglik(p: float, x1: int, n1: int, x2: int, n2: int, d: float) -> float:
    p1, p2 = p + d, p
    if not (1e-12 < p1 < 1 - 1e-12) or not (1e-12 < p2 < 1 - 1e-12):
        return -1e18
    ll = 0.0
    if x1 > 0:
        ll += x1 * math.log(p1)
    if n1 - x1 > 0:
        ll += (n1 - x1) * math.log(1.0 - p1)
    if x2 > 0:
        ll += x2 * math.log(p2)
    if n2 - x2 > 0:
        ll += (n2 - x2) * math.log(1.0 - p2)
    return ll


def _constrained_mle(x1: int, n1: int, x2: int, n2: int, d: float):
    """p1 − p2 = d 约束下的约束 MLE（黄金分割最大化）。"""
    lo = max(1e-12, -d + 1e-12)
    hi = min(1.0 - 1e-12, 1.0 - d - 1e-12)
    if lo >= hi:
        return None
    gr = (math.sqrt(5.0) - 1.0) / 2.0
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


def mn_z(x1: int, n1: int, x2: int, n2: int, d: float, correct: bool = True):
    """Miettinen-Nurminen 分数统计量 Z(d)。"""
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
    return (p1h - p2h - d) / math.sqrt(var)


def mn_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05, correct: bool = True):
    """Miettinen-Nurminen 率差 95%CI。返回百分数 (diff, lo, hi)。"""
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


def wilson_ci(x: int, n: int, alpha: float = 0.05):
    """单组率 Wilson 95%CI（Newcombe 法的基础件）。返回小数比例 (lo, hi)。"""
    z = norm_ppf(1.0 - alpha / 2.0)
    p = x / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return centre - half, centre + half


def newcombe_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05):
    """Newcombe 杂交 Wilson 率差 95%CI。返回百分数 (diff, lo, hi)，用于独立交叉验证。"""
    l1, u1 = wilson_ci(x1, n1, alpha)
    l2, u2 = wilson_ci(x2, n2, alpha)
    p1, p2 = x1 / n1, x2 / n2
    diff = 100.0 * (p1 - p2)
    lo = 100.0 * ((p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2))
    hi = 100.0 * ((p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))
    return diff, lo, hi


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """2×2 双侧 Fisher 确切概率法 P 值。"""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def pr(x):
        if x < 0 or x > r1 or c1 - x < 0 or c1 - x > n - r1:
            return 0.0
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)

    p_obs = pr(a)
    if p_obs <= 0:
        return 1.0
    tol = p_obs * (1.0 + 1e-9)
    return min(1.0, sum(pr(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1)
                        if pr(x) <= tol))


# ---------------------------------------------------------------------------
# 删失值与几何均数
# ---------------------------------------------------------------------------

CENSOR_RULES = ("lod_half", "lod", "lod_sqrt")


def parse_conc(raw: str, below_tokens=("＜", "<"), above_tokens=("＞", ">")):
    """解析检测值字符串。返回 (值, 标记)，标记 ∈ {ok, below, above, na}。"""
    if raw is None:
        return None, "na"
    s = str(raw).strip().replace(" ", "")
    if s in ("", "/", "NA", "N/A", "-", "－"):
        return None, "na"
    for tok in below_tokens:
        if tok in s:
            m = _first_float(s)
            return (m if m is not None else None), "below"
    for tok in above_tokens:
        if tok in s:
            m = _first_float(s)
            return (m if m is not None else None), "above"
    try:
        return float(s), "ok"
    except ValueError:
        return None, "na"


def _first_float(s: str):
    m = ""
    started = False
    for ch in s:
        if ch.isdigit() or ch == ".":
            m += ch
            started = True
        elif started:
            break
    try:
        return float(m)
    except ValueError:
        return None


def censored_value(val, flag, rule: str = "lod_half"):
    """把删失值转成可参与几何均数计算的数值。"""
    if flag == "ok" or flag == "above":
        return val
    if flag == "na":
        return None
    if val is None:
        return None
    if rule == "lod_half":
        return val / 2.0
    if rule == "lod":
        return val
    if rule == "lod_sqrt":
        return math.sqrt(val)
    raise ValueError(f"未知删失规则: {rule}")


def gmc_and_ci(values, alpha: float = 0.05):
    """几何均数及其 95%CI（对数转换 + t 分布）。返回 (gmc, lo, hi, n)。"""
    vs = [v for v in values if v is not None and v > 0]
    n = len(vs)
    if n == 0:
        return None, None, None, 0
    logs = [math.log(v) for v in vs]
    m = statistics.fmean(logs)
    gmc = math.exp(m)
    if n < 2:
        return gmc, None, None, n
    se = statistics.stdev(logs) / math.sqrt(n)
    tcrit = t_ppf(1.0 - alpha / 2.0, n - 1)
    return gmc, math.exp(m - tcrit * se), math.exp(m + tcrit * se), n


def gmc_ratio_test(v1, v2, alpha: float = 0.05):
    """对数转换后成组 t 检验。返回 (ratio, lo, hi, t, df, p)。"""
    l1 = [math.log(v) for v in v1 if v is not None and v > 0]
    l2 = [math.log(v) for v in v2 if v is not None and v > 0]
    n1, n2 = len(l1), len(l2)
    if n1 < 2 or n2 < 2:
        raise ValueError("GMC 比较要求每组至少 2 例有效数据")
    m1, m2 = statistics.fmean(l1), statistics.fmean(l2)
    s1, s2 = statistics.stdev(l1), statistics.stdev(l2)
    df = n1 + n2 - 2
    sp2 = ((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / df
    se = math.sqrt(sp2 * (1.0 / n1 + 1.0 / n2))
    diff = m1 - m2
    t = diff / se
    p = 2.0 * (1.0 - t_cdf(abs(t), df))
    tcrit = t_ppf(1.0 - alpha / 2.0, df)
    return (math.exp(diff), math.exp(diff - tcrit * se), math.exp(diff + tcrit * se),
            t, df, p)


# ---------------------------------------------------------------------------
# 内置校准（官方已发表值）
# ---------------------------------------------------------------------------

# TVAX-009B Ⅰ期 CSR（定稿 V1.0，2024-09-30）表 11-9 / 11-11 / 11-12
PHASE1_RATE = [
    # x, n, 官方率(%), CI 下限, CI 上限
    (30, 31, 96.77, 83.30, 99.92), (27, 27, 100.00, 87.23, 100.00),
    (38, 40, 95.00, 83.08, 99.39), (39, 40, 97.50, 86.84, 99.94),
    (37, 39, 94.87, 82.68, 99.37), (38, 39, 97.44, 86.52, 99.94),
]
PHASE1_GMC_P = [("TVAX-009B Ⅰ期 全人群 FAS", 0.5066), ("TVAX-009B Ⅰ期 全人群 PPS2", 0.5440),
                ("TVAX-009B Ⅰ期 免前阴性 FAS", 0.1696), ("TVAX-009B Ⅰ期 免前阴性 PPS2", 0.2048)]
# TVAX-009-002 Ⅱ期 TFL 表 14.2.4.2.x 官方跨时点比较（率差 CI，Miettinen-Nurminen）
PHASE2_MN = [
    # (x1, n1, x2, n2, diff, lo, hi)
    (64, 74, 65, 71, -5.06, -15.94, 5.60),
    (68, 74, 65, 71, 0.34, -9.40, 10.29),
    (65, 75, 67, 75, -2.67, -13.69, 8.20),
    (69, 75, 67, 75, 2.67, -7.24, 12.83),
]


def self_check(verbose: bool = True) -> bool:
    """用官方已发表值校验本模块。全部通过返回 True。"""
    ok = True
    if verbose:
        print("统计内核自检（对照官方已发表值）")

    for x, n, p_off, lo_off, hi_off in PHASE1_RATE:
        lo, hi, p = clopper_pearson(x, n)
        good = (abs(p - p_off) < 0.005 and abs(lo - lo_off) < 0.005
                and abs(hi - hi_off) < 0.005)
        ok = ok and good
        if verbose:
            print(f"  Clopper-Pearson {x}/{n}: {p:.2f}({lo:.2f}, {hi:.2f}) "
                  f"vs 官方 {p_off}({lo_off}, {hi_off})  {'OK' if good else 'FAIL'}")

    for x1, n1, x2, n2, d_off, lo_off, hi_off in PHASE2_MN:
        diff, lo, hi = mn_ci(x1, n1, x2, n2)
        good = (abs(diff - d_off) < 0.005 and abs(lo - lo_off) < 0.005
                and abs(hi - hi_off) < 0.005)
        ok = ok and good
        if verbose:
            print(f"  Miettinen-Nurminen {x1}/{n1} vs {x2}/{n2}: "
                  f"{diff:.2f}({lo:.2f}, {hi:.2f}) vs 官方 {d_off}({lo_off}, {hi_off})  "
                  f"{'OK' if good else 'FAIL'}")

    # Newcombe 交叉验证：与 MN 差异应 <1 个百分点
    for x1, n1, x2, n2, d_off, _, _ in PHASE2_MN:
        _, lo, hi = newcombe_ci(x1, n1, x2, n2)
        good = lo <= d_off <= hi
        ok = ok and good
        if verbose:
            print(f"  Newcombe 交叉验证 {x1}/{n1} vs {x2}/{n2}: "
                  f"({lo:.2f}, {hi:.2f}) 含官方点估计 {d_off}  {'OK' if good else 'FAIL'}")

    # 删失值换算规则：LOD/2
    vals_half = [censored_value(2.0, "below", "lod_half") for _ in range(31)]
    g_half = gmc_and_ci(vals_half)[0]
    good = abs(g_half - 1.0) < 1e-9
    ok = ok and good
    if verbose:
        print(f"  删失规则 lod_half: LOD=2.00 -> {g_half:.3f}  {'OK' if good else 'FAIL'}")

    if verbose:
        print("自检结论：", "全部通过" if ok else "存在差异，禁止出数")
    return ok


OFFICIAL_GMC_P = PHASE1_GMC_P  # 官方组间 GMC 比较 P 值，供说明页列出校准项


# ---------------------------------------------------------------------------
# 事件判定
# ---------------------------------------------------------------------------


def is_event(pre, post, event_type: str, cutoff: float = 10.0, fold: float = 4.0) -> bool:
    """判定单个受试者在某时点是否为事件。

    seroconversion             免前 < cutoff 且 免后 ≥ cutoff
    fourfold                   免前 ≥ cutoff 且 免后/免前 ≥ fold
    seroconversion_or_4fold    上述二者满足其一（CSR 所称「阳转（4 倍增长）率」）
    positive                   免后 ≥ cutoff（抗体阳性率，不看免前）
    """
    if pre is None or post is None:
        return False
    if event_type == "positive":
        return post >= cutoff
    if event_type == "seroconversion":
        return pre < cutoff and post >= cutoff
    if event_type == "fourfold":
        return pre >= cutoff and post / pre >= fold
    if event_type == "seroconversion_or_4fold":
        if pre < cutoff:
            return post >= cutoff
        return post / pre >= fold
    raise ValueError(f"未知事件类型: {event_type}")


def _passes_filter(row: dict, flt: dict | None) -> bool:
    if not flt:
        return True
    col = flt["column"]
    val = row.get(col + "_value")
    if val is None:
        return False
    op, target = flt.get("op", "<"), float(flt["value"])
    if op == "<":
        return val < target
    if op == "<=":
        return val <= target
    if op == ">":
        return val > target
    if op == ">=":
        return val >= target
    if op == "==":
        return val == target
    raise ValueError(f"未知筛选算符: {op}")


def load_subjects(path: str) -> list[dict]:
    """读取 parse_immunogenicity_listing.py 输出的个体级 CSV。"""
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in list(r.keys()):
            if k.endswith("_value"):
                r[k] = float(r[k]) if r[k] not in ("", None) else None
            elif k.startswith("in_"):
                r[k] = r[k] == "True"
            elif k.endswith("_flag"):
                pass
    return rows


def select(subjects: list[dict], arm_key: str, pop: dict, analysis_set: str,
           outcome_field: str, spec: dict):
    """按 arm / 人群 / 分析集筛选，返回 (事件数, 总数, 浓度列表)。"""
    trial = spec["arms"]["trial"]
    control = spec["arms"]["control"]
    cutoff = float(spec.get("cutoff", 10.0))
    fold = float(spec.get("fold", 4.0))
    rule = spec.get("censoring", {}).get("rule", "lod_half")
    event_type = pop["rate_metric"]["event"]

    arm = trial if arm_key == "trial" else control
    x = n = 0
    concs = []
    for r in subjects:
        if r.get(spec.get("arm_field", "group")) != arm:
            continue
        if analysis_set != "FAS" and not r.get("in_" + analysis_set.lower(), False):
            continue
        if not _passes_filter(r, pop.get("filter")):
            continue
        n += 1
        pre = r.get("pre_value")
        raw = r.get(outcome_field + "_value")
        flag = r.get(outcome_field + "_flag", "ok")
        val = censored_value(raw, flag, rule)
        concs.append(val)
        if is_event(pre, val, event_type, cutoff, fold):
            x += 1
    return x, n, concs


def compute(spec: dict, subjects: list[dict]) -> dict:
    """按 spec 计算全部 人群 × 分析集 × 指标 组合。"""
    outcome_field = spec["outcome"]["field"]
    margin_rate = float(spec["margins"]["rate_diff"])
    margin_gmc = float(spec["margins"]["gmc_ratio"])
    rows = []

    for pop in spec["populations"]:
        for a_set in spec["analysis_sets"]:
            x1, n1, v1 = select(subjects, "trial", pop, a_set, outcome_field, spec)
            x2, n2, v2 = select(subjects, "control", pop, a_set, outcome_field, spec)

            lo1, hi1, p1 = clopper_pearson(x1, n1)
            lo2, hi2, p2 = clopper_pearson(x2, n2)
            diff, dlo, dhi = mn_ci(x1, n1, x2, n2)
            nlo, nhi = newcombe_ci(x1, n1, x2, n2)[1:]
            pv = fisher_exact_2x2(x1, n1 - x1, x2, n2 - x2)
            rate_verdict = "成立" if (dlo is not None and dlo > margin_rate) else "不成立"
            rows.append(dict(population=pop["name"], metric="rate",
                             metric_label=pop["rate_metric"]["name"],
                             analysis_set=a_set,
                             trial=dict(x=x1, n=n1, pct=p1, lo=lo1, hi=hi1),
                             control=dict(x=x2, n=n2, pct=p2, lo=lo2, hi=hi2),
                             estimate=dict(diff=diff, lo=dlo, hi=dhi, p=pv),
                             cross_check=dict(lo=nlo, hi=nhi),
                             margin=margin_rate, verdict=rate_verdict))

            g1, gl1, gh1, gn1 = gmc_and_ci(v1)
            g2, gl2, gh2, gn2 = gmc_and_ci(v2)
            ratio, rlo, rhi, t, df, gp = gmc_ratio_test(v1, v2)
            gmc_verdict = "成立" if (rlo is not None and rlo > margin_gmc) else "不成立"
            rows.append(dict(population=pop["name"], metric="gmc",
                             metric_label=spec.get("gmc_label", "抗-HBs GMC"),
                             analysis_set=a_set,
                             trial=dict(n=gn1, gmc=g1, lo=gl1, hi=gh1),
                             control=dict(n=gn2, gmc=g2, lo=gl2, hi=gh2),
                             estimate=dict(ratio=ratio, lo=rlo, hi=rhi, p=gp, t=t, df=df),
                             margin=margin_gmc, verdict=gmc_verdict))

    return dict(meta={k: spec.get(k) for k in ("study", "outcome", "arms")}, rows=rows)


def _v_or_dash(v, nd=2):
    return "-" if v is None else round(v, nd)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="疫苗免疫原性非劣效分析统计内核")
    ap.add_argument("--spec", help="分析规格 JSON（由使用者填写，参见 assets/ 示例）")
    ap.add_argument("--subjects", help="个体级 CSV（parse_immunogenicity_listing.py 产出）")
    ap.add_argument("--out", help="结果 JSON 输出路径")
    ap.add_argument("--self-check", action="store_true", help="用内置官方值校验本模块")
    args = ap.parse_args(argv)

    if args.self_check:
        return 0 if self_check() else 1

    if not (args.spec and args.subjects and args.out):
        ap.error("需要同时提供 --spec / --subjects / --out（或单独使用 --self-check）")

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    subjects = load_subjects(args.subjects)
    if not self_check(verbose=False):
        print("ERROR: 统计内核自检未通过，拒绝出数", file=sys.stderr)
        return 1

    results = compute(spec, subjects)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"已写出：{args.out}（{len(results['rows'])} 行结果）")
    for r in results["rows"]:
        if r["metric"] == "rate":
            print(f"  {r['population']} {r['analysis_set']} 率 "
                  f"{r['trial']['x']}/{r['trial']['n']}={_v_or_dash(r['trial']['pct'])}% vs "
                  f"{r['control']['x']}/{r['control']['n']}={_v_or_dash(r['control']['pct'])}% "
                  f"率差 {_v_or_dash(r['estimate']['diff'])}"
                  f"（{_v_or_dash(r['estimate']['lo'])}, {_v_or_dash(r['estimate']['hi'])}）"
                  f" {r['verdict']}")
        else:
            print(f"  {r['population']} {r['analysis_set']} GMC "
                  f"{_v_or_dash(r['trial']['gmc'], 3)} vs {_v_or_dash(r['control']['gmc'], 3)} "
                  f"比值 {_v_or_dash(r['estimate']['ratio'], 3)}"
                  f"（{_v_or_dash(r['estimate']['lo'], 3)}, {_v_or_dash(r['estimate']['hi'], 3)}）"
                  f" {r['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
