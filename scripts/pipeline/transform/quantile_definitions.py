"""Sample quantile definitions for reconciling Q1/Median/Q3 against SAS TFL output.

Retrospective biostatistical cross-checking utility. Different software uses
different percentile definitions, which is the most common root cause of
Q1/Q3 mismatches between an independently programmed TFL and the
statistician's SAS output. This module implements:

* SAS ``PCTLDEF=1..5`` exactly as documented for ``PROC UNIVARIATE`` /
  ``PROC MEANS`` (``5`` is the SAS default),
* Tukey hinges (exclusive and inclusive median for odd ``n``),
* linear interpolation (R type 7 / NumPy / Excel ``QUARTILE.INC``).

Pure standard library; exact arithmetic on ``n*p`` via :class:`fractions.Fraction`.

CLI::

    python scripts/pipeline/transform/quantile_definitions.py 3 5 7 8 12 13 14 18 21 --target-q1 7 --target-q3 14
"""

from __future__ import annotations

import argparse
import math
from fractions import Fraction
from typing import Iterable, Sequence

__all__ = [
    "QUANTILE_DEFINITIONS",
    "median",
    "quantile",
    "quartiles",
    "scan_definitions",
]

QUANTILE_DEFINITIONS: tuple[str, ...] = (
    "sas1", "sas2", "sas3", "sas4", "sas5", "tukey", "tukey_inc", "linear",
)


def _sorted_values(values: Iterable[float | int | None]) -> list[float]:
    out: list[float] = []
    for v in values:
        if v is None:
            continue
        f = float(v)
        if math.isnan(f):
            continue
        out.append(f)
    out.sort()
    return out


def median(values: Iterable[float | int | None]) -> float | None:
    """Median ignoring ``None``/NaN; ``None`` for an empty input."""
    s = _sorted_values(values)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _y(s: Sequence[float], i: int) -> float:
    """1-based order statistic with SAS boundary convention y0 = y1, y(n+1) = yn."""
    n = len(s)
    return s[min(max(i, 1), n) - 1]


def _sas(s: Sequence[float], p: Fraction, definition: int) -> float:
    n = len(s)
    np_ = (n + 1) * p if definition == 4 else n * p
    j = math.floor(np_)
    g = np_ - j
    if definition in (1, 4):
        return float((1 - g) * Fraction(_y(s, j)) + g * Fraction(_y(s, j + 1)))
    if definition == 2:
        if g == Fraction(1, 2):
            i = j if j % 2 == 0 else j + 1
        else:
            i = math.floor(np_ + Fraction(1, 2))
        return _y(s, i)
    if definition == 3:
        return _y(s, j) if g == 0 else _y(s, j + 1)
    if definition == 5:
        return (_y(s, j) + _y(s, j + 1)) / 2.0 if g == 0 else _y(s, j + 1)
    raise ValueError(f"SAS PCTLDEF must be 1..5, got {definition}")


def quantile(values: Iterable[float | int | None], p: float, definition: str = "sas5") -> float | None:
    """Return the ``p``-quantile (0 <= p <= 1) of ``values`` under ``definition``.

    ``definition`` is one of :data:`QUANTILE_DEFINITIONS`. Tukey variants only
    support ``p`` in {0.25, 0.5, 0.75}.
    """
    if not 0 <= p <= 1:
        raise ValueError(f"p must be within [0, 1], got {p}")
    s = _sorted_values(values)
    n = len(s)
    if n == 0:
        return None
    pf = Fraction(str(p))

    if definition.startswith("sas"):
        try:
            num = int(definition[3:])
        except ValueError as exc:
            raise ValueError(f"unknown definition {definition!r}") from exc
        return _sas(s, pf, num)

    if definition == "linear":
        idx = pf * (n - 1)
        lo = math.floor(idx)
        hi = min(lo + 1, n - 1)
        g = idx - lo
        return float(Fraction(s[lo]) + g * (Fraction(s[hi]) - Fraction(s[lo])))

    if definition in ("tukey", "tukey_inc"):
        if pf == Fraction(1, 2):
            return median(s)
        if pf not in (Fraction(1, 4), Fraction(3, 4)):
            raise ValueError("Tukey hinges are only defined for p in {0.25, 0.5, 0.75}")
        if definition == "tukey":  # exclude the median for odd n (Moore & McCabe)
            low, high = s[: n // 2], s[(n + 1) // 2:]
        else:  # include the median for odd n (Tukey's original hinges)
            low, high = s[: (n + 1) // 2], s[n // 2:]
        half = low if pf == Fraction(1, 4) else high
        return median(half) if half else s[0]

    raise ValueError(f"unknown definition {definition!r}; choose from {QUANTILE_DEFINITIONS}")


def quartiles(values: Iterable[float | int | None], definition: str = "sas5") -> tuple[float | None, float | None, float | None]:
    """Return ``(Q1, Median, Q3)`` under ``definition`` (median is definition-independent)."""
    s = _sorted_values(values)
    return quantile(s, 0.25, definition), median(s), quantile(s, 0.75, definition)


def scan_definitions(
    values: Iterable[float | int | None],
    target_q1: float | None = None,
    target_q3: float | None = None,
    tol: float = 0.005,
) -> list[dict[str, float | str | bool | None]]:
    """Evaluate every definition; flag those matching the target Q1/Q3 within ``tol``."""
    s = _sorted_values(values)
    rows: list[dict[str, float | str | bool | None]] = []
    for name in QUANTILE_DEFINITIONS:
        q1, _, q3 = quartiles(s, name)
        match: bool | None = None
        if target_q1 is not None or target_q3 is not None:
            match = True
            if target_q1 is not None:
                match = match and q1 is not None and abs(q1 - target_q1) <= tol
            if target_q3 is not None:
                match = match and q3 is not None and abs(q3 - target_q3) <= tol
        rows.append({"definition": name, "q1": q1, "q3": q3, "match": match})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare quartile definitions against target Q1/Q3.")
    parser.add_argument("values", type=float, nargs="+")
    parser.add_argument("--target-q1", type=float)
    parser.add_argument("--target-q3", type=float)
    parser.add_argument("--tol", type=float, default=0.005)
    args = parser.parse_args(argv)

    print(f"n = {len(args.values)}  median = {median(args.values)}")
    for r in scan_definitions(args.values, args.target_q1, args.target_q3, args.tol):
        flag = "" if r["match"] is None else ("  MATCH" if r["match"] else "")
        print(f"  {r['definition']:<10} Q1 = {r['q1']!s:<12} Q3 = {r['q3']!s:<12}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
