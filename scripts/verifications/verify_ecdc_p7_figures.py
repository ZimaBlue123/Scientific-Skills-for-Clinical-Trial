"""Verify the ECDC 2022 figures quoted on slide 7 (25-54: 6.3-9.7;
55-64: 5.8; >=65: 3.7 per 100,000) against the archived ECDC PDF."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

PDF = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "文献库-F2F Meeting"
    / "01_立题依据-流行病学与接种策略"
    / "ECDC_Hepatitis-B-Annual-Epidemiological-Report-2022.pdf"
)
OUT = Path(__file__).with_name("_ecdc_check.txt")

PATS = [
    r"25[-–]54",
    r"55[-–]64",
    r"65",
    r"6\.3",
    r"9\.7",
    r"5\.8",
    r"3\.7",
    r"age group",
    r"notification rate",
]

_buf: list[str] = []
reader = PdfReader(str(PDF))
text = "\n".join((p.extract_text() or "") for p in reader.pages)
flat = re.sub(r"\s+", " ", text)
_buf.append(f"pages={len(reader.pages)} chars={len(text)}")
for pat in PATS:
    hits = re.findall(pat, flat, re.IGNORECASE)
    _buf.append(f"[{pat}] -> {len(hits)}")
_buf.append("")
for m in re.finditer(r"(25[-–]54|55[-–]64|65\s*years)", flat, re.IGNORECASE):
    s = max(0, m.start() - 220)
    _buf.append("  ..." + flat[s : m.end() + 220] + "...")
    _buf.append("")
OUT.write_text("\n".join(_buf), encoding="utf-8")
