"""Encoding validation utilities."""

from __future__ import annotations

import logging
from pathlib import Path

from ..extract.text_normalizer import MOJIBAKE_MARKERS, _is_pua

logger = logging.getLogger(__name__)

def check_bom(path: Path | str) -> bool:
    """Check if file starts with a UTF-8 Byte Order Mark (BOM)."""
    with open(path, "rb") as f:
        return f.read(3) == b"\\xef\\xbb\\xbf"

def diagnose_encoding(path: Path | str) -> dict:
    """Check a file for mojibake and encoding issues."""
    try:
        raw = open(path, "rb").read()
    except OSError:
        return {"status": "error", "message": "Cannot read file"}

    if b"\\x00" in raw[:4096]:
        return {"status": "binary"}

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"status": "not-utf8"}

    pua = sum(1 for c in text if _is_pua(c))
    markers = sum(1 for c in text if c in MOJIBAKE_MARKERS)

    if pua > 0 or markers >= 5:
        return {
            "status": "mojibake",
            "pua_count": pua,
            "marker_count": markers
        }

    return {"status": "ok"}

__all__ = ["check_bom", "diagnose_encoding"]
