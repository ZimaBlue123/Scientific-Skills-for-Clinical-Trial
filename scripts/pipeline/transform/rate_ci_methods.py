"""Binomial proportion and rate-difference confidence intervals for TFL cross-verification.

Retrospective biostatistical cross-checking utility: reproduces the interval
methods commonly used by SAS ``PROC FREQ`` (``BINOMIAL`` / ``RISKDIFF``) so that
response-rate tables in CSR/TFL deliverables can be reconciled against the
statistician's authoritative output. Pure standard library (no SciPy needed).

Single proportion:
    ``wilson_ci``, ``wilson_cc_ci``, ``clopper_pearson_ci``, ``wald_ci``
Rate difference (p1 - p2):
    ``wald_diff_ci``, ``wald_cc_diff_ci``, ``newcombe_diff_ci``,
    ``agresti_caffo_diff_ci``, ``hauck_anderson_diff_ci``,
    ``miettinen_nurminen_diff_ci`` (``mee=True`` gives Mee's variant)

All functions return proportions on the 0-1 scale; multiply by 100 for %.

CLI (scan every method against an authoritative target CI, in percent)::

    python scripts/pipeline/transform/rate_ci_methods.py 10 30 8 28 --target -20.48 28.76
"""

from __future__ import annotations

import argparse
import math
from statistics import NormalDist
from typing import Callable

__all__ = [
    "z_value",
    "wald_ci",
    "wilson_ci",
    "wilson_cc_ci",
    "clopper_pearson_ci",
    "wald_diff_ci",
    "wald_cc_diff_ci",
    "newcombe_diff_ci",
    "agresti_caffo_diff_ci",
    "hauck_anderson_diff_ci",
    "miettinen_nurminen_diff_ci",
    "DIFF_METHODS",
    "scan_diff_methods",
]

Interval = tuple[float, float]


def _check(x: int, n: int) -> None:
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= x <= n:
        raise ValueError(f"x must satisfy 0 <= x <= n, got x={x}, n={n}")


def z_value(alpha: float = 0.05) -> float:
    """Two-sided standard-normal critical value for ``alpha``."""
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    return NormalDist().inv_cdf(1 - alpha / 2)


def _clip(lo: float, hi: float, low: float = 0.0, high: float = 1.0) -> Interval:
    return max(low, lo), min(high, hi)


# ---------------------------------------------------------------------------
# Single proportion
# ---------------------------------------------------------------------------


def wald_ci(x: int, n: int, alpha: float = 0.05) -> Interval:
    """Asymptotic Wald interval (SAS ``BINOMIAL`` default), clipped to [0, 1]."""
    _check(x, n)
    z = z_value(alpha)
    p = x / n
    h = z * math.sqrt(p * (1 - p) / n)
    return _clip(p - h, p + h)


def wilson_ci(x: int, n: int, alpha: float = 0.05) -> Interval:
    """Wilson score interval without continuity correction."""
    _check(x, n)
    z = z_value(alpha)
    p = x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return _clip(centre - half, centre + half)


def wilson_cc_ci(x: int, n: int, alpha: float = 0.05) -> Interval:
    """Wilson score interval with continuity correction (Newcombe 1998, method 4)."""
    _check(x, n)
    z = z_value(alpha)
    z2 = z * z
    p = x / n
    den = 2 * (n + z2)
    if x == 0:
        lo = 0.0
    else:
        lo = (2 * n * p + z2 - 1 - z * math.sqrt(z2 - 2 - 1 / n + 4 * p * (n * (1 - p) + 1))) / den
    if x == n:
        hi = 1.0
    else:
        hi = (2 * n * p + z2 + 1 + z * math.sqrt(z2 + 2 - 1 / n + 4 * p * (n * (1 - p) - 1))) / den
    return _clip(lo, hi)


def _binom_log_pmf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 0.0 if k == 0 else -math.inf
    if p >= 1.0:
        return 0.0 if k == n else -math.inf
    return (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        + k * math.log(p) + (n - k) * math.log1p(-p)
    )


def _binom_cdf(x: int, n: int, p: float) -> float:
    """P(X <= x) for X ~ Bin(n, p)."""
    return min(1.0, sum(math.exp(_binom_log_pmf(k, n, p)) for k in range(0, x + 1)))


def _bisect(f: Callable[[float], float], lo: float, hi: float, tol: float = 1e-12, max_iter: int = 300) -> float:
    """Root of a monotone function with ``f(lo)`` and ``f(hi)`` of opposite sign."""
    flo = f(lo)
    if flo == 0:
        return lo
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        fm = f(mid)
        if fm == 0 or (hi - lo) < tol:
            return mid
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson_ci(x: int, n: int, alpha: float = 0.05) -> Interval:
    """Exact Clopper-Pearson interval (SAS ``BINOMIAL(EXACT)``)."""
    _check(x, n)
    a2 = alpha / 2
    # lower: P(X >= x | p) = a2  <=>  1 - cdf(x-1) = a2
    lo = 0.0 if x == 0 else _bisect(lambda p: (1 - _binom_cdf(x - 1, n, p)) - a2, 0.0, 1.0)
    # upper: P(X <= x | p) = a2
    hi = 1.0 if x == n else _bisect(lambda p: _binom_cdf(x, n, p) - a2, 0.0, 1.0)
    return lo, hi


# ---------------------------------------------------------------------------
# Rate difference p1 - p2
# ---------------------------------------------------------------------------


def wald_diff_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> Interval:
    """Asymptotic Wald interval for p1 - p2 (SAS ``RISKDIFF`` default)."""
    _check(x1, n1)
    _check(x2, n2)
    z = z_value(alpha)
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return _clip(d - z * se, d + z * se, -1.0, 1.0)


def wald_cc_diff_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> Interval:
    """Wald interval with Yates-type continuity correction ``(1/n1 + 1/n2) / 2``."""
    _check(x1, n1)
    _check(x2, n2)
    z = z_value(alpha)
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    cc = 0.5 * (1 / n1 + 1 / n2)
    d = p1 - p2
    return _clip(d - z * se - cc, d + z * se + cc, -1.0, 1.0)


_SINGLE_FOR_NEWCOMBE: dict[str, Callable[[int, int, float], Interval]] = {
    "wilson": wilson_ci,
    "wilson_cc": wilson_cc_ci,
    "clopper_pearson": clopper_pearson_ci,
}


def newcombe_diff_ci(
    x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05, kind: str = "wilson"
) -> Interval:
    """Newcombe hybrid score interval (``kind``: wilson | wilson_cc | clopper_pearson)."""
    _check(x1, n1)
    _check(x2, n2)
    try:
        single = _SINGLE_FOR_NEWCOMBE[kind]
    except KeyError as exc:
        raise ValueError(f"unknown Newcombe kind {kind!r}; choose from {sorted(_SINGLE_FOR_NEWCOMBE)}") from exc
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = single(x1, n1, alpha)
    l2, u2 = single(x2, n2, alpha)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return lo, hi


def agresti_caffo_diff_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> Interval:
    """Agresti-Caffo interval (add one success and one failure per group)."""
    _check(x1, n1)
    _check(x2, n2)
    z = z_value(alpha)
    p1 = (x1 + 1) / (n1 + 2)
    p2 = (x2 + 1) / (n2 + 2)
    se = math.sqrt(p1 * (1 - p1) / (n1 + 2) + p2 * (1 - p2) / (n2 + 2))
    d = p1 - p2
    return _clip(d - z * se, d + z * se, -1.0, 1.0)


def hauck_anderson_diff_ci(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> Interval:
    """Hauck-Anderson interval (SAS ``RISKDIFF(CL=HA)``)."""
    _check(x1, n1)
    _check(x2, n2)
    if n1 < 2 or n2 < 2:
        raise ValueError("Hauck-Anderson requires n1 >= 2 and n2 >= 2")
    z = z_value(alpha)
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / (n1 - 1) + p2 * (1 - p2) / (n2 - 1))
    cc = 1.0 / (2 * min(n1, n2))
    d = p1 - p2
    return _clip(d - z * se - cc, d + z * se + cc, -1.0, 1.0)


def _restricted_mle(x1: int, n1: int, x2: int, n2: int, delta: float) -> tuple[float, float]:
    """Restricted MLE (p1~, p2~) under H0: p1 - p2 = delta (Farrington-Manning closed form)."""
    p1h, p2h = x1 / n1, x2 / n2
    theta = n2 / n1
    a = 1 + theta
    b = -(1 + theta + p1h + theta * p2h + delta * (theta + 2))
    c = delta * delta + delta * (2 * p1h + theta + 1) + p1h + theta * p2h
    d = -p1h * delta * (1 + delta)
    v = b ** 3 / (27 * a ** 3) - b * c / (6 * a * a) + d / (2 * a)
    disc = b * b / (9 * a * a) - c / (3 * a)
    u = math.copysign(math.sqrt(max(disc, 0.0)), v) if v != 0 else math.sqrt(max(disc, 0.0))
    if u == 0:
        p1t = -b / (3 * a)
    else:
        ratio = max(-1.0, min(1.0, v / u ** 3))
        w = (math.pi + math.acos(ratio)) / 3
        p1t = 2 * u * math.cos(w) - b / (3 * a)
    p1t = min(max(p1t, 0.0), 1.0)
    p2t = min(max(p1t - delta, 0.0), 1.0)
    return p1t, p2t


def miettinen_nurminen_diff_ci(
    x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05, mee: bool = False
) -> Interval:
    """Miettinen-Nurminen score interval (SAS ``RISKDIFF(CL=MN)``); ``mee=True`` drops N/(N-1)."""
    _check(x1, n1)
    _check(x2, n2)
    z = z_value(alpha)
    d_hat = x1 / n1 - x2 / n2
    big_n = n1 + n2
    factor = 1.0 if mee or big_n < 2 else big_n / (big_n - 1)
    eps = 1e-10

    def score(delta: float) -> float:
        p1t, p2t = _restricted_mle(x1, n1, x2, n2, delta)
        var = (p1t * (1 - p1t) / n1 + p2t * (1 - p2t) / n2) * factor
        if var <= 0:
            return math.inf if d_hat > delta else (-math.inf if d_hat < delta else 0.0)
        return (d_hat - delta) / math.sqrt(var)

    lo = -1.0 if d_hat <= -1 + eps else _bisect(lambda dl: score(dl) - z, -1 + eps, d_hat)
    hi = 1.0 if d_hat >= 1 - eps else _bisect(lambda dl: score(dl) + z, d_hat, 1 - eps)
    return lo, hi


DIFF_METHODS: dict[str, Callable[..., Interval]] = {
    "Wald": wald_diff_ci,
    "Wald+cc": wald_cc_diff_ci,
    "Newcombe-Wilson": lambda *a, **k: newcombe_diff_ci(*a, kind="wilson", **k),
    "Newcombe-Wilson+cc": lambda *a, **k: newcombe_diff_ci(*a, kind="wilson_cc", **k),
    "Newcombe-CP": lambda *a, **k: newcombe_diff_ci(*a, kind="clopper_pearson", **k),
    "Agresti-Caffo": agresti_caffo_diff_ci,
    "Hauck-Anderson": hauck_anderson_diff_ci,
    "Miettinen-Nurminen": miettinen_nurminen_diff_ci,
    "Mee": lambda *a, **k: miettinen_nurminen_diff_ci(*a, mee=True, **k),
}


def scan_diff_methods(
    x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05, target_pct: Interval | None = None
) -> list[dict[str, float | str | None]]:
    """Evaluate every rate-difference method; optionally rank by max abs error vs ``target_pct``."""
    rows: list[dict[str, float | str | None]] = []
    for name, fn in DIFF_METHODS.items():
        try:
            lo, hi = fn(x1, n1, x2, n2, alpha=alpha)
        except (ValueError, ZeroDivisionError) as exc:
            rows.append({"method": name, "lower_pct": None, "upper_pct": None, "max_abs_err_pp": None, "error": str(exc)})
            continue
        err = None
        if target_pct is not None:
            err = max(abs(lo * 100 - target_pct[0]), abs(hi * 100 - target_pct[1]))
        rows.append({"method": name, "lower_pct": lo * 100, "upper_pct": hi * 100, "max_abs_err_pp": err, "error": None})
    if target_pct is not None:
        rows.sort(key=lambda r: math.inf if r["max_abs_err_pp"] is None else r["max_abs_err_pp"])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan rate-difference CI methods against a target CI.")
    parser.add_argument("x1", type=int)
    parser.add_argument("n1", type=int)
    parser.add_argument("x2", type=int)
    parser.add_argument("n2", type=int)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--target", type=float, nargs=2, metavar=("LOWER_PCT", "UPPER_PCT"),
                        help="authoritative CI in percent, e.g. --target -20.48 28.76")
    args = parser.parse_args(argv)

    target = tuple(args.target) if args.target else None
    rows = scan_diff_methods(args.x1, args.n1, args.x2, args.n2, alpha=args.alpha, target_pct=target)
    diff = (args.x1 / args.n1 - args.x2 / args.n2) * 100
    print(f"{args.x1}/{args.n1} vs {args.x2}/{args.n2}  diff = {diff:.2f} pp  target = {target}")
    for r in rows:
        if r["error"]:
            print(f"  {r['method']:<20} n/a ({r['error']})")
            continue
        err = "" if r["max_abs_err_pp"] is None else f"  max|err| = {r['max_abs_err_pp']:.3f} pp"
        print(f"  {r['method']:<20} ({r['lower_pct']:8.2f}, {r['upper_pct']:8.2f}){err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
