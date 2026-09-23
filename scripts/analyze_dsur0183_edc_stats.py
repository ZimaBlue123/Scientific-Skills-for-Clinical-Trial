#!/usr/bin/env python3
"""Compute DSUR cross-check statistics from the TVAX-018-3 EDC export.

Produces review_materials/018-3/_work/refs/edc_stats.md with:
  * enrolment / exposure counts
  * demographics by age band and sex
  * AE counts: total, solicited/local/systemic, unsolicited, onset within 60 min,
    grade >= 3, outcome, relatedness, duration
  * SAE listing

Usage
-----
    py -3 scripts/analyze_dsur0183_edc_stats.py
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "review_materials" / "018-3" / "前期资料"
OUT = ROOT / "review_materials" / "018-3" / "_work" / "refs" / "edc_stats.md"

XLSX = next((p for p in SRC.iterdir() if p.name.startswith("YDSWXTVAX-018-3-001")), None)


def rows(ws):
    """Row 1 = Chinese label, row 2 = SDTM variable name, data from row 3."""
    header = [c.value for c in ws[2]]
    for r in ws.iter_rows(min_row=3, values_only=True):
        yield dict(zip(header, r))


def main() -> int:
    if XLSX is None:
        return 2
    wb = load_workbook(XLSX, data_only=True)
    out: list[str] = ["# EDC cross-check statistics", ""]

    # ---- demographics ----
    dm = wb["dm"]
    sexes = Counter()
    ages = []
    enrolled = 0
    for rec in rows(dm):
        if str(rec.get("SUBJ_STATUS") or "").strip() != "已入组":
            continue
        enrolled += 1
        sex = rec.get("SEX")
        age = rec.get("AGE")
        try:
            sex_i = int(str(sex).strip())
            age_i = int(float(str(age).strip()))
        except (TypeError, ValueError):
            continue
        sexes[sex_i] += 1
        ages.append((age_i, sex_i))
    out.append(f"- 已入组受试者记录数: {enrolled}")
    out.append("## Demographics (dm)")
    out.append(f"- 男(1)={sexes.get(1, 0)}  女(2)={sexes.get(2, 0)}  合计={sum(sexes.values())}")
    bands = Counter()
    band_sex = Counter()
    for age, sex in ages:
        band = "18-59" if age < 60 else ">=60"
        bands[band] += 1
        band_sex[(band, sex)] += 1
    for band in ("18-59", ">=60"):
        out.append(
            f"- {band}: 合计={bands[band]} 男={band_sex[(band, 1)]} 女={band_sex[(band, 2)]}"
        )
    out.append(f"- 年龄范围: {min(a for a, _ in ages)} - {max(a for a, _ in ages)}")
    out.append("")

    # ---- AE ----
    ae = wb["ae"]
    recs = list(rows(ae))
    out.append("## AE (ae)")
    out.append(f"- AE 记录数(例次): {len(recs)}")
    subs = {r.get("FIELD1") for r in recs if r.get("FIELD1")}
    out.append(f"- 涉及受试者数(例): {len(subs)}")

    def cnt(field, value):
        return sum(1 for r in recs if str(r.get(field)).strip() == str(value))

    out.append(f"- 征集性(AECAT=2): {cnt('AECAT', 2)}  非征集性(AECAT=1): {cnt('AECAT', 1)}")
    out.append(
        f"- 接种部位局部(AEZCAT=1): {cnt('AEZCAT', 1)}  全身(AEZCAT=2): {cnt('AEZCAT', 2)}"
    )
    out.append(f"- 接种后60分钟内发生(AETPTYN=2): {cnt('AETPTYN', 2)}")
    for label, col in (
        ("严重程度", "AETOXGR"),
        ("转归", "AEOUT"),
        ("相关性", "AEREL"),
        ("治疗情况", "AEACNOTH"),
        ("是否导致提前退出", "AEDIS"),
    ):
        c = Counter(r.get(col) for r in recs)
        out.append(f"- {label}: {dict(c)}")
    sol = Counter()
    for r in recs:
        if str(r.get("AECAT")).strip() == "2":
            name = r.get("AETERMJ_DESC") or r.get("AETERMQ_DESC") or r.get("AETERM")
            sol[name] += 1
    out.append("- 征集性 AE 症状分布:")
    for k, v in sol.most_common():
        out.append(f"    - {k}: {v}")

    term = Counter(r.get("AETERM") for r in recs)
    out.append("- AE 名称(PT) 分布:")
    for k, v in term.most_common():
        out.append(f"    - {k}: {v}")
    grade3 = [r for r in recs if str(r.get("AETOXGR")).strip() == "3"]
    out.append(f"- 3级 AE 明细(共{len(grade3)}):")
    for r in grade3:
        out.append(
            f"    - {r.get('FIELD1')} {r.get('AETERM')} 级别={r.get('AETOXGR')} "
            f"剂次={r.get('AEDOSEC')} 相关性={r.get('AEREL')} 转归={r.get('AEOUT')}"
        )
    minutes = [r for r in recs if str(r.get("AETPTYN")).strip() == "2"]
    out.append(f"- 免后60min AE 明细(共{len(minutes)}):")
    for r in minutes:
        name = r.get("AETERMJ_DESC") or r.get("AETERMQ_DESC") or r.get("AETERM")
        out.append(
            f"    - {r.get('FIELD1')} {name} 级别={r.get('AETOXGR')} 征集性={r.get('AECAT')} "
            f"剂次={r.get('AEDOSEC')} 治疗={r.get('AEACNOTH')} 转归={r.get('AEOUT')}"
        )
    min_terms = Counter(
        (r.get("AETERMJ_DESC") or r.get("AETERMQ_DESC") or r.get("AETERM")) for r in minutes
    )
    out.append(f"- 免后60min AE 症状分布: {dict(min_terms)}")
    min_subs = {r.get("FIELD1") for r in minutes}
    out.append(f"- 免后60min AE 涉及受试者数: {len(min_subs)} ({sorted(min_subs)})")
    def num(v):
        try:
            return float(str(v).strip())
        except (TypeError, ValueError):
            return None

    dur = [x for x in (num(r.get("AEDAYB")) for r in recs) if x is not None]
    if dur:
        out.append(f"- AE 持续天数: min={min(dur):.0f} max={max(dur):.0f} 记录数={len(dur)}")
    onset = [x for x in (num(r.get("AEDAYA")) for r in recs) if x is not None]
    within7 = sum(1 for x in onset if 0 <= x <= 7)
    out.append(f"- 接种后0-7天内发生: {within7}/{len(onset)} ({within7 / len(onset):.1%})")
    not_recovered = [r for r in recs if str(r.get("AEOUT")).strip() not in ("1", "None")]
    out.append(f"- 非'痊愈'转归 AE 明细(共{len(not_recovered)}):")
    for r in not_recovered:
        name = r.get("AETERMJ_DESC") or r.get("AETERMQ_DESC") or r.get("AETERM")
        out.append(
            f"    - {r.get('FIELD1')} {name} 征集性={r.get('AECAT')} 转归={r.get('AEOUT_DESC')} "
            f"级别={r.get('AETOXGR')} 持续={r.get('AEDAYB')}天 相关性={r.get('AEREL_DESC')}"
        )
    out.append("")

    # ---- SAE (aes) ----
    aes = wb["aes"]
    sae = list(rows(aes))
    out.append("## SAE (aes)")
    out.append(f"- SAE 记录数: {len(sae)}")
    for r in sae:
        out.append("    - " + " | ".join(f"{k}={v}" for k, v in r.items() if v not in (None, "")))
    out.append("")

    # ---- disposition ----
    dseos = wb["dseos"]
    out.append("## Disposition (dseos)")
    withdraw = []
    for r in rows(dseos):
        if str(r.get("DSYN")).strip() == "1":
            withdraw.append(r)
    out.append(f"- 未完成/退出例数: {len(withdraw)}")
    for r in withdraw:
        out.append(
            f"    - {r.get('FIELD1')} 日期={r.get('DSSTDAT')} "
            f"原因={r.get('DSDECOD')}/{r.get('DSDECOD_DESC')} 说明={r.get('DSTERM')}"
        )
    out.append("")
    out.append(f"_generated: {datetime.now():%Y-%m-%d %H:%M}_")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
