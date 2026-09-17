#!/usr/bin/env python3
"""Probe Chinese journal article pages for a real PDF URL.

The magtech-based journal sites hide the PDF behind a JS handler, so the raw
HTML is fetched and scanned for absolute/relative PDF paths, then candidate
URLs are tested with a HEAD/GET request.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
OUT = ROOT / "scripts" / "_pdf_probe.txt"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

PAGES = [
    "https://www.lcgdbzz.com/article/doi/10.12449/JCH240808",
    "https://www.lcgdbzz.org/article/doi/10.12449/JCH240808",
    "https://www.zgggws.com/article/doi/10.11847/zgggws1132715",
]

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


for url in PAGES:
    log("=" * 90)
    log(url)
    try:
        status, body = fetch(url)
    except Exception as exc:  # noqa: BLE001
        log(f"  FETCH ERROR: {exc}")
        continue
    log(f"  status={status} bytes={len(body)}")
    try:
        text = body.decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        text = body.decode("latin-1", "ignore")
    hits = set(re.findall(r"[\"']([^\"']{4,200}?\.pdf[^\"']{0,60})[\"']", text, re.IGNORECASE))
    hits |= set(
        re.findall(
            r"(?:href|src)=[\"']([^\"']*?(?:download|pdf)"
            r"[^\"']*)[\"']",
            text,
            re.IGNORECASE,
        )
    )
    log(f"  pdf-like references: {len(hits)}")
    for h in sorted(hits)[:25]:
        log(f"    {h}")
    if not hits:
        log("  (none) -- showing first 400 chars of body:")
        log("    " + re.sub(r"\s+", " ", text)[:400])

OUT.write_text("\n".join(_log), encoding="utf-8")
