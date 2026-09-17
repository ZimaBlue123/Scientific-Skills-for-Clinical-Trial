"""Probe for the full-text endpoints of the two Chinese-journal references that
are still missing from the library:

1. 中华预防医学会《成人乙型肝炎疫苗接种专家建议》(2024) — lcgdbzz.com loads the
   body via JS, so the raw HTML is scanned for the full-text endpoint.
2. 张国民等《中国2005-2016年乙型病毒性肝炎报告发病的年龄和地区特征》— the CNKI
   journal platform exposes abstracts; the article link (paperID) is extracted.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
OUT = ROOT / "scripts" / "_fulltext_probe.txt"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

_log: list[str] = []


def log(m: str) -> None:
    _log.append(m)


def get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", "ignore")


# ---------------------------------------------------------------- 1 lcgdbzz
log("=" * 90)
log("lcgdbzz full-text endpoint probe")
try:
    status, raw = get("https://www.lcgdbzz.com/article/doi/10.12449/JCH240808")
    log(f"status={status} bytes={len(raw)}")
    pats = [
        r"[\w/\.\-]*(?:fullText|fulltext|FullText|viewType|articleContent)"
        r"[\w/\.\-\?=&%]*",
        r"[\w/\.\-]*paperDigest[\w/\.\-\?=&%]*",
        r"[\w/\.\-]*/article/[\w/\.\-]*",
    ]
    seen: set[str] = set()
    for pat in pats:
        for m in re.findall(pat, raw):
            if m not in seen:
                seen.add(m)
                log(f"  {m}")
except Exception as exc:  # noqa: BLE001
    log(f"  ERROR {exc}")

# ---------------------------------------------------------------- 2 zgjm
log("=" * 90)
log("zgjm (中国疫苗和免疫 2018;24(2)) article links")
try:
    status, raw = get(
        "https://zgjm.cbpt.cnki.net/WKD/WebPublication/wkTextContent.aspx?colType=4&yt=2018&st=02"
    )
    log(f"status={status} bytes={len(raw)}")
    links = re.findall(
        r"[\w/\.\-]*(?:paperDigest|wkTextContent)"
        r"[\w/\.\-\?=&%;]*",
        raw,
    )
    seen = set()
    for m in links:
        if m not in seen:
            seen.add(m)
            log(f"  {m}")
    idx = raw.find("张国民")
    log(f"  '张国民' at {idx}")
    if idx > 0:
        log("  context: " + re.sub(r"\s+", " ", raw[idx - 600 : idx + 600]))
except Exception as exc:  # noqa: BLE001
    log(f"  ERROR {exc}")

OUT.write_text("\n".join(_log), encoding="utf-8")
