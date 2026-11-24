"""Immunogenicity endpoint statistics for vaccine clinical TFLs.

Generic building blocks shared by baseline-stratified / overall immunogenicity
analyses (anti-HBs seroconversion, seroresponse, GMC, GMI) with the conventions
used by the sponsor's statistical report:

* left-censored values (``<LLOQ``) are imputed at ``LLOQ/2`` for GMC / GMI
* proportion CIs use Clopper-Pearson (exact)
* log-transformed group comparison uses the pooled-variance (Student) t test
* 2x2 comparison uses Pearson chi-square without continuity correction;
  Fisher exact test is used when any expected cell count is < 5
* rate-difference CI uses Newcombe-Wilson (hybrid score, no continuity correction)

Public API
----------
``ProportionResult`` / ``GeoMeanResult`` / ``GroupComparison`` dataclasses,
``proportion``, ``geomean``, ``compare_proportions``, ``compare_log_means``,
``rate_difference_ci``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from scipy import stats as _st


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class ProportionResult:
    n: int          # numerator (responders)
    N: int          # denominator (evaluable)
    rate: float | None
    ci_low: float | None
    ci_high: float | None


@dataclass
class GeoMeanResult:
    n: int
    gmean: float | None
    ci_low: float | None
    ci_high: float | None
    logs: list[float]


@dataclass
class GroupComparison:
    method: str
    statistic: float | None
    p_value: float | None
    diff: float | None = None
    diff_ci_low: float | None = None
    diff_ci_high: float | None = None


# --------------------------------------------------------------------------- #
# Core estimators
# --------------------------------------------------------------------------- #
def proportion(n: int, N: int, alpha: float = 0.05) -> ProportionResult:
    """Exact (Clopper-Pearson) CI for a binomial proportion, returned in %."""
    if N == 0:
        return ProportionResult(n, N, None, None, None)
    rate = n / N
    if n == 0:
        lo, hi = 0.0, 1 - (alpha / 2) ** (1 / N)
    elif n == N:
        lo, hi = (alpha / 2) ** (1 / N), 1.0
    else:
        lo = _st.beta.ppf(alpha / 2, n, N - n + 1)
        hi = _st.beta.ppf(1 - alpha / 2, n + 1, N - n)
    return ProportionResult(n, N, rate * 100, lo * 100, min(hi, 1.0) * 100)


def geomean(values: Sequence[float], alpha: float = 0.05) -> GeoMeanResult:
    """Geometric mean with a log-normal (t based) CI."""
    vals = [v for v in values if v is not None and v > 0]
    n = len(vals)
    if n == 0:
        return GeoMeanResult(0, None, None, None, [])
    logs = [math.log(v) for v in vals]
    m = sum(logs) / n
    gm = math.exp(m)
    if n == 1:
        return GeoMeanResult(n, gm, None, None, logs)
    sd = math.sqrt(sum((x - m) ** 2 for x in logs) / (n - 1))
    se = sd / math.sqrt(n)
    tcrit = _st.t.ppf(1 - alpha / 2, n - 1)
    return GeoMeanResult(n, gm, math.exp(m - tcrit * se), math.exp(m + tcrit * se), logs)


# --------------------------------------------------------------------------- #
# Group comparisons
# --------------------------------------------------------------------------- #
def rate_difference_ci(
    n1: int, N1: int, n2: int, N2: int, alpha: float = 0.05
) -> tuple[float, float, float]:
    """Newcombe-Wilson hybrid score CI for p1 - p2 (percent units)."""
    if N1 == 0 or N2 == 0:
        return (0.0, 0.0, 0.0)
    p1, p2 = n1 / N1, n2 / N2
    d = p1 - p2
    # Wilson score intervals for the two arms
    z = _st.norm.ppf(1 - alpha / 2)

    def wilson(n: int, N: int) -> tuple[float, float]:
        p = n / N
        denom = 1 + z * z / N
        centre = (p + z * z / (2 * N)) / denom
        half = z * math.sqrt(p * (1 - p) / N + z * z / (4 * N * N)) / denom
        return max(0.0, centre - half), min(1.0, centre + half)

    l1, u1 = wilson(n1, N1)
    l2, u2 = wilson(n2, N2)
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (d * 100, lo * 100, hi * 100)


def compare_proportions(n1: int, N1: int, n2: int, N2: int, alpha: float = 0.05) -> GroupComparison:
    """Pearson chi-square (no correction), falling back to Fisher exact when
    any expected cell count < 5. Returns rate difference and its CI as well."""
    if N1 == 0 or N2 == 0:
        return GroupComparison("无法检验", None, None)
    table = [[n1, N1 - n1], [n2, N2 - n2]]
    total = N1 + N2
    r1, r2 = N1, N2
    c1, c2 = n1 + n2, (N1 - n1) + (N2 - n2)
    expected = [
        r1 * c1 / total, r1 * c2 / total,
        r2 * c1 / total, r2 * c2 / total,
    ]
    diff, lo, hi = rate_difference_ci(n1, N1, n2, N2, alpha)
    if min(expected) < 5:
        _, p = _st.fisher_exact(table)
        return GroupComparison("Fisher确切概率法", None, p, diff, lo, hi)
    chi2 = total * (n1 * (N2 - n2) - (N1 - n1) * n2) ** 2 / (r1 * r2 * c1 * c2)
    p = 1 - _st.chi2.cdf(chi2, 1)
    return GroupComparison("卡方检验", chi2, p, diff, lo, hi)


def compare_log_means(g1: GeoMeanResult, g2: GeoMeanResult) -> GroupComparison:
    """Pooled-variance (Student) t test on log-transformed values."""
    if g1.n < 2 or g2.n < 2:
        return GroupComparison("成组t检验", None, None)
    m1 = sum(g1.logs) / g1.n
    m2 = sum(g2.logs) / g2.n
    ss1 = sum((x - m1) ** 2 for x in g1.logs)
    ss2 = sum((x - m2) ** 2 for x in g2.logs)
    df = g1.n + g2.n - 2
    sp2 = (ss1 + ss2) / df
    se = math.sqrt(sp2 * (1 / g1.n + 1 / g2.n))
    if se == 0:
        return GroupComparison("成组t检验", None, None)
    t = (m1 - m2) / se
    p = 2 * (1 - _st.t.cdf(abs(t), df))
    return GroupComparison("成组t检验", t, p)


# --------------------------------------------------------------------------- #
# Formatting helpers (report conventions: rates 2 dp, P 4 dp, GMC 3 dp)
# --------------------------------------------------------------------------- #
def fmt_rate(res: ProportionResult) -> str:
    if res.rate is None:
        return "-"
    return f"{res.n} ({res.rate:.2f})"


def fmt_ci(low, high, digits: int = 2) -> str:
    if low is None or high is None:
        return "-"
    return f"{low:.{digits}f}, {high:.{digits}f}"


def fmt_p(p: float | None) -> str:
    if p is None:
        return "NA"
    if p < 0.0001:
        return "<0.0001"
    return f"{p:.4f}"


# --------------------------------------------------------------------------- #
# Sample size & power calculations for non-inferiority (NI) bridging trials
# --------------------------------------------------------------------------- #
def _restricted_mle_p2(p1: float, p2: float, delta0: float, ratio: float = 1.0) -> float:
    """Restricted MLE of control rate ``p2`` under ``H0: p1 - p2 = delta0``."""
    from scipy.optimize import brentq

    def score(p2x: float) -> float:
        p1x = p2x + delta0
        return (p1x - p1) * ratio + (p2x - p2)

    lo = max(1e-6, -delta0 + 1e-6)
    hi = min(1.0 - 1e-6, 1.0 - delta0 - 1e-6)
    if lo >= hi:
        return p2
    try:
        return float(brentq(score, lo, hi))
    except ValueError:
        return p2


def sample_size_rate_ni_wald(
    p_test: float,
    p_ctrl: float,
    margin: float,
    alpha_one_sided: float = 0.025,
    power: float = 0.90,
    ratio: float = 1.0,
) -> tuple[int, int]:
    """Unpooled Wald sample size ``(n_ctrl, n_test)`` for rate-difference NI."""
    if margin <= 0:
        raise ValueError(f"margin must be positive (absolute NI margin), got {margin}")
    z_a = float(_st.norm.ppf(1.0 - alpha_one_sided))
    z_b = float(_st.norm.ppf(power))
    delta = p_test - p_ctrl
    eff = margin + delta
    if eff <= 0:
        raise ValueError(f"Effective margin (margin + p_test - p_ctrl) must be > 0, got {eff}")
    var_term = p_test * (1.0 - p_test) / ratio + p_ctrl * (1.0 - p_ctrl)
    n_ctrl = math.ceil(((z_a + z_b) ** 2) * var_term / (eff**2))
    n_test = math.ceil(n_ctrl * ratio)
    return n_ctrl, n_test


def power_rate_ni_fm(
    n_ctrl: float,
    p_test: float,
    p_ctrl: float,
    margin: float,
    alpha_one_sided: float = 0.025,
    ratio: float = 1.0,
) -> float:
    """Farrington-Manning score test power for rate-difference non-inferiority."""
    n_test = n_ctrl * ratio
    delta0 = -abs(margin)
    z_a = float(_st.norm.ppf(1.0 - alpha_one_sided))
    p2h = _restricted_mle_p2(p_test, p_ctrl, delta0, ratio)
    p1h = p2h + delta0
    se0_sq = p1h * (1.0 - p1h) / n_test + p2h * (1.0 - p2h) / n_ctrl
    se1_sq = p_test * (1.0 - p_test) / n_test + p_ctrl * (1.0 - p_ctrl) / n_ctrl
    if se0_sq <= 0 or se1_sq <= 0:
        return 0.0
    se0, se1 = math.sqrt(se0_sq), math.sqrt(se1_sq)
    z = (p_test - p_ctrl - delta0) / se1 - z_a * se0 / se1
    return float(_st.norm.cdf(z))


def sample_size_rate_ni_fm(
    p_test: float,
    p_ctrl: float,
    margin: float,
    alpha_one_sided: float = 0.025,
    power: float = 0.90,
    ratio: float = 1.0,
) -> tuple[int, int]:
    """Farrington-Manning score test sample size ``(n_ctrl, n_test)`` for rate-difference NI."""
    from scipy.optimize import brentq

    if margin <= 0:
        raise ValueError(f"margin must be positive (absolute NI margin), got {margin}")
    lo, hi = 2.0, 5e6
    if power_rate_ni_fm(lo, p_test, p_ctrl, margin, alpha_one_sided, ratio) >= power:
        n_ctrl = int(math.ceil(lo))
    else:
        n_ctrl = int(
            math.ceil(
                brentq(
                    lambda x: power_rate_ni_fm(x, p_test, p_ctrl, margin, alpha_one_sided, ratio) - power,
                    lo,
                    hi,
                )
            )
        )
    return n_ctrl, int(math.ceil(n_ctrl * ratio))


def sample_size_gmc_ni(
    ratio_expected: float,
    margin_ratio: float,
    sigma_ln: float,
    alpha_one_sided: float = 0.025,
    power: float = 0.90,
    ratio: float = 1.0,
) -> tuple[int, int]:
    """Sample size ``(n_ctrl, n_test)`` for GMC ratio non-inferiority on the natural-log scale."""
    if not (0 < margin_ratio < ratio_expected):
        raise ValueError("Require 0 < margin_ratio < ratio_expected for GMC NI sample size")
    z_a = float(_st.norm.ppf(1.0 - alpha_one_sided))
    z_b = float(_st.norm.ppf(power))
    diff_ln = math.log(ratio_expected) - math.log(margin_ratio)
    factor = 1.0 + 1.0 / ratio
    n_ctrl = int(math.ceil(factor * (sigma_ln**2) * ((z_a + z_b) ** 2) / (diff_ln**2)))
    return n_ctrl, int(math.ceil(n_ctrl * ratio))


def power_gmc_ni(
    n_ctrl: int,
    ratio_expected: float,
    margin_ratio: float,
    sigma_ln: float,
    alpha_one_sided: float = 0.025,
    ratio: float = 1.0,
) -> float:
    """Power for GMC ratio non-inferiority on the natural-log scale."""
    z_a = float(_st.norm.ppf(1.0 - alpha_one_sided))
    se = sigma_ln * math.sqrt(1.0 / n_ctrl + 1.0 / (n_ctrl * ratio))
    if se <= 0:
        return 0.0
    z = (math.log(ratio_expected) - math.log(margin_ratio)) / se - z_a
    return float(_st.norm.cdf(z))


def simulate_gmc_ni_pass_rate(
    n_eval_per_arm: int,
    ratio_expected: float,
    sigma_ln: float,
    margins: Sequence[float] = (2.0 / 3.0,),
    n_sim: int = 100_000,
    alpha_two_sided: float = 0.05,
    seed: int | None = None,
    rng=None,
) -> dict:
    """Monte-Carlo pass rate of a GMC-ratio non-inferiority test (equal arms).

    Draws the sufficient statistics (sample mean ~ Normal, sample variance ~
    scaled chi-square) on the natural-log scale for both arms, builds the
    pooled-variance Student-t two-sided CI of the log GMC ratio and checks the
    lower bound against each margin in ``margins``.

    Pass an explicit ``rng`` (``numpy.random.Generator``) to share one draw
    sequence across several scenarios (reproducible multi-scenario runs);
    otherwise a fresh generator is created from ``seed``.

    Returns a dict with ``pass_rate`` (``{margin: rate}``), lower-bound ratio
    median / 5th percentile, theoretical vs simulated SE and the expected CI.
    """
    import numpy as np

    if n_eval_per_arm < 2:
        raise ValueError("n_eval_per_arm must be >= 2")
    if ratio_expected <= 0 or sigma_ln <= 0:
        raise ValueError("ratio_expected and sigma_ln must be > 0")
    if n_sim < 1:
        raise ValueError("n_sim must be >= 1")
    if any(m <= 0 for m in margins):
        raise ValueError("all margins must be > 0")

    gen = rng if rng is not None else np.random.default_rng(seed)
    n = n_eval_per_arm
    df = 2 * n - 2
    t_crit = float(_st.t.ppf(1.0 - alpha_two_sided / 2.0, df))
    mu = math.log(ratio_expected)

    z1 = gen.standard_normal(n_sim)
    z2 = gen.standard_normal(n_sim)
    chi1 = gen.chisquare(n - 1, n_sim)
    chi2 = gen.chisquare(n - 1, n_sim)
    y1 = mu + sigma_ln / math.sqrt(n) * z1
    y2 = sigma_ln / math.sqrt(n) * z2
    s1sq = sigma_ln**2 * chi1 / (n - 1)
    s2sq = sigma_ln**2 * chi2 / (n - 1)
    sp = np.sqrt(((n - 1) * s1sq + (n - 1) * s2sq) / df)
    se = sp * math.sqrt(2.0 / n)
    lower_ln = (y1 - y2) - t_crit * se
    lower_ratio = np.exp(lower_ln)
    se_theory = sigma_ln * math.sqrt(2.0 / n)

    return {
        "pass_rate": {float(m): float((lower_ln >= math.log(m)).mean()) for m in margins},
        "lower_ratio_median": float(np.median(lower_ratio)),
        "lower_ratio_p05": float(np.percentile(lower_ratio, 5)),
        "se_theory": se_theory,
        "se_sim_mean": float(se.mean()),
        "t_crit": t_crit,
        "expected_ci": (
            math.exp(mu - t_crit * se_theory),
            math.exp(mu + t_crit * se_theory),
        ),
    }


__all__ = [
    "ProportionResult",
    "GeoMeanResult",
    "GroupComparison",
    "proportion",
    "geomean",
    "rate_difference_ci",
    "compare_proportions",
    "compare_log_means",
    "fmt_rate",
    "fmt_ci",
    "fmt_p",
    "sample_size_rate_ni_wald",
    "power_rate_ni_fm",
    "sample_size_rate_ni_fm",
    "sample_size_gmc_ni",
    "power_gmc_ni",
    "simulate_gmc_ni_pass_rate",
]
