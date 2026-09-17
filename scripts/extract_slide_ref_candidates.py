"""Targeted extraction for the candidate source PDFs of the slide
"成人乙肝疫苗接种面临的挑战与新型疫苗立题依据".

For each candidate file: dump the first page (title/abstract) plus keyword-in-context
hits for the slide's specific figures.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

LIB = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "文献库-F2F Meeting"
)
OUT = Path(__file__).with_name("_slide_refs_targeted.txt")

TARGETS = [
    LIB
    / "03_免疫程序-2针vs3针与依从性"
    / "其他2针 VS 3针与依从性的相关文献"
    / "Adult_HBV_Vaccination_Coverage_in_China_2011-2021-2022.pdf",
    LIB
    / "02_同类产品-CpG佐剂与对照疫苗"
    / "其他乙肝原研产品"
    / "康泰60ug乙肝疫苗临床探索"
    / "乙肝预防重心需向成人转移 - 深圳康泰生物制品股份有限公司.pdf",
    LIB / "01_立题依据-流行病学与接种策略" / "ChinaCDCWeekly_Acute-Hepatitis-B-China-2005-2019.pdf",
    LIB
    / "01_立题依据-流行病学与接种策略"
    / "PMID 41780552_Seroepidemiology_HBV_China_nationwide-ClinMolHepatol-2026.pdf",
    LIB / "04_特殊人群-肾透析-糖尿病-低应答" / "CDC2011_HepB-vaccination-diabetes-MMWR6051.pdf",
    LIB
    / "04_特殊人群-肾透析-糖尿病-低应答"
    / "PMID 23173138_Schillie_HepB-immune-response-diabetes-systematic-review.pdf",
    LIB
    / "03_免疫程序-2针vs3针与依从性"
    / "其他2针 VS 3针与依从性的相关文献"
    / "成人乙肝疫苗全程接种影响因素及免疫效果调查-2025.pdf",
    LIB
    / "03_免疫程序-2针vs3针与依从性"
    / "其他2针 VS 3针与依从性的相关文献"
    / "乙型肝炎疫苗2针免疫程序研究进展-2025.pdf",
]

KEYWORDS = [
    r"14\.7",
    r"2\.98",
    r"2\.94",
    r"2\.93",
    r"96",
    r"2\s*[~～\-–—到至]\s*3\s*倍",
    r"2 to 3",
    r"twofold|two-fold|2-fold|3-fold",
    r"母婴|mother-to-child|perinatal",
    r"南方|south",
    r"欠发达|develop",
    r"男.{0,10}女|male",
    r"肾功能|renal|kidney",
    r"糖尿病|diabet",
    r"0[，,\s\-–—]*1[，,\s\-–—]*6|3 剂|three.dose",
    r"60|elderly|old",
    r"依从|complet|adheren",
    r"消除|elimin|WHO",
    r"接种率|coverage",
]

_buf: list[str] = []


def out(*args) -> None:
    _buf.append(" ".join(str(a) for a in args))


for pdf in TARGETS:
    out("=" * 100)
    rel = pdf.relative_to(LIB) if pdf.exists() else pdf
    out("FILE:", rel)
    if not pdf.exists():
        out("  MISSING")
        continue
    try:
        reader = PdfReader(str(pdf))
        pages = [(pg.extract_text() or "") for pg in reader.pages]
    except Exception as exc:  # noqa: BLE001
        out("  READ ERROR:", exc)
        continue
    out(f"  pages={len(pages)}")
    # first two pages verbatim (title / abstract usually carries the key claims)
    for i, t in enumerate(pages[:2]):
        out(f"  ---- page {i + 1} (verbatim, first 3500 chars) ----")
        out(re.sub(r"\n{3,}", "\n\n", t.strip()[:3500]))
    flat = re.sub(r"\s+", " ", "\n".join(pages))
    out("  ---- keyword-in-context (whole doc) ----")
    seen: set[str] = set()
    for kw in KEYWORDS:
        for m in re.finditer(kw, flat, re.IGNORECASE):
            s = max(0, m.start() - 130)
            e = min(len(flat), m.end() + 130)
            ctx = flat[s:e]
            key = ctx[:70]
            if key in seen:
                continue
            seen.add(key)
            out(f"    [{kw}]")
            out(f"      ...{ctx}...")
            if len(seen) > 90:
                break
        if len(seen) > 90:
            break
OUT.write_text("\n".join(_buf), encoding="utf-8")
