"""Verify the newly archived PDFs: confirm they carry the data quoted on
slides 7 and 8 (age-specific incidence, recommendation wording)."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

BASE = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "文献库-F2F Meeting"
    / "01_立题依据-流行病学与接种策略"
)
OUT = Path(__file__).with_name("_verify_new_refs.txt")

PROBES = {
    "蒋伟2022_中国大陆居民2004-2017年乙肝发病趋势_中国公共卫生-38(3)-257-261.pdf": [
        r"211\.00",
        r"181\.62",
        r"163\.11",
        r"12\.78",
        r"80\.21",
        r"AAPC",
    ],
    "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf": [
        r"18\s*[~～]\s*59",
        r"60",
        r"0-1-6|0、1、6",
        r"20\s*μg|20μg",
    ],
    "CDC_2023_Hepatitis-Surveillance_Figure2-4_Acute-HepB-Rates-by-Age.pdf": [
        r"Figure 2\.4",
        r"40–49|40-49",
        r"2023",
    ],
}

_buf: list[str] = []


def log(m: str) -> None:
    _buf.append(m)


for name, pats in PROBES.items():
    path = BASE / name
    log("=" * 90)
    log(f"{name}  exists={path.exists()}")
    if not path.exists():
        continue
    try:
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:  # noqa: BLE001
        log(f"  READ ERROR {exc}")
        continue
    log(f"  pages={len(reader.pages)} chars={len(text)}")
    for pat in pats:
        hits = re.findall(pat, text)
        log(f"  [{pat}] -> {len(hits)} hit(s)")
        for h in hits[:5]:
            log(f"      {h if isinstance(h, str) else h}")
    log("  --- head 900 chars ---")
    log("  " + re.sub(r"\s+", " ", text[:900]))

OUT.write_text("\n".join(_buf), encoding="utf-8")
