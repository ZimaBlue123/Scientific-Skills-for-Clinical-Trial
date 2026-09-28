#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_ics_literature_timepoints.py

Purpose
-------
Extract text from the ICS / cellular-immunity reference PDFs under
``review_materials/02_抗原特异性多细胞因子ICS`` and pull out every sentence /
table line that mentions a sampling time point or response kinetics, so that we
can judge when antigen-specific cytokine responses (IFN-g, IL-2, TNF-a, ...)
reach their peak after vaccination.

Usage
-----
    python scripts/extract_ics_literature_timepoints.py                # full scan
    python scripts/extract_ics_literature_timepoints.py --dump         # dump raw text
    python scripts/extract_ics_literature_timepoints.py --kw "day 7"   # custom keyword

Output
------
    reports/lit_timepoints/<pdf_stem>.txt        (raw text, with --dump)
    stdout: grouped hits per PDF
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "review_materials" / "02_抗原特异性多细胞因子ICS"
OUT_DIR = ROOT / "reports" / "lit_timepoints"

# Keywords indicating a sampling / kinetics time point.
TIME_KW = [
    r"\bday\s*\d+", r"\bd\s*\d+\b", r"\bweek\s*\d+", r"\bw\s*\d+\b",
    r"\bmonth\s*\d+", r"\bpost(?:\s|-)?(?:vaccination|vaccine|immuni\w+|boost|dose|injection)",
    r"\bpre(?:\s|-)?(?:vaccination|vaccine|immuni\w+|dose|bleed)",
    r"\bbaseline", r"\bpeak\b", r"\bkinetics?\b", r"\btime\s*point", r"\btimepoint",
    r"\bfollow[-\s]?up", r"\bafter\s+(?:the\s+)?(?:first|second|third|1st|2nd|3rd|last)\s+(?:dose|immuni\w+|vaccination)",
    r"\b\d+\s*(?:h|hr|hrs|hours|days|weeks|months)\s+(?:after|post|following)",
    r"\b\d+\s*(?:hours?|days?|weeks?|months?)\b",
]
TIME_RE = re.compile("|".join(TIME_KW), re.I)

# Cytokines / readouts of interest.
MARKER_RE = re.compile(
    r"\b(IFN|IL|TNF|IP-10|CXCL10|MIP|CD107|CD154|CD137|4-1BB|OX40|CD69|granzyme|GZB|perforin)\b",
    re.I,
)


def extract_text(pdf: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    parts = []
    for i, page in enumerate(reader.pages, 1):
        try:
            t = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover
            t = f"[page {i} extraction failed: {exc}]"
        parts.append(f"\n===== PAGE {i} =====\n{t}")
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true", help="also write raw text to reports/lit_timepoints")
    ap.add_argument("--kw", action="append", default=[], help="extra keyword (regex) to search")
    ap.add_argument("--pattern", default=None, help="only process PDFs whose name matches")
    args = ap.parse_args()

    pats = TIME_KW + args.kw
    rx = re.compile("|".join(pats), re.I)

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if args.pattern:
        pdfs = [p for p in pdfs if re.search(args.pattern, p.name, re.I)]
    if not pdfs:
        print(f"no PDF found under {PDF_DIR}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf in pdfs:
        print("\n" + "#" * 90)
        print(f"# FILE: {pdf.name}")
        print("#" * 90)
        text = extract_text(pdf)
        if args.dump:
            (OUT_DIR / f"{pdf.stem}.txt").write_text(text, encoding="utf-8")
            print(f"[raw text -> {OUT_DIR / (pdf.stem + '.txt')}]  chars={len(text)}")

        hits = []
        for para in re.split(r"\n+", text):
            p = para.strip()
            if len(p) < 20:
                continue
            if rx.search(p) and (MARKER_RE.search(p) or re.search(r"\b(peak|kinetics?|time ?point)\b", p, re.I)):
                hits.append(p)
        if not hits:
            print("(no time-point + marker hit)")
        for h in hits[:80]:
            print("-", re.sub(r"\s+", " ", h))
        print(f"[total hits: {len(hits)} / paragraphs scanned]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
