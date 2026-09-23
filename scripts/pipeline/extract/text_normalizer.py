"""Text normalization and encoding diagnostics."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

MOJIBAKE_MARKERS = set(
    "涓锛鈥鏂瀹绾鍜鐨缁璁鍑铏鍏璺绛鎴鍦ㄩ噸"
    "椤圭洰氫綅闅愮搴擄紙寮虹儓鏈熷熀叏鍗曟枃"
    "鎵弿鍒犻櫎浜ゆ槗嶅悓姝ュ垪鏍纺鐢ヨ旈熶"
    "鐩爜铻嶈繍缂撴潯鑺傛暟鎹璁扮"
)

def _is_pua(ch: str) -> bool:
    return 0xE000 <= ord(ch) <= 0xF8FF

def detect_encoding(raw_bytes: bytes) -> str:
    """Guess the encoding of raw bytes."""
    if raw_bytes.startswith(b"\\xef\\xbb\\xbf"):
        return "utf-8-sig"
    try:
        raw_bytes.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass  # Intentional: not UTF-8, fall through to the next candidate encoding.
    try:
        raw_bytes.decode("gb18030")
        return "gb18030"
    except UnicodeDecodeError:
        pass  # Intentional: not GB18030 either; the latin-1 fallback below always decodes.
    return "latin-1"

def fix_mojibake(text: str) -> str:
    """Identify and attempt to fix common mojibake patterns.
    
    Checks for Private Use Area (PUA) characters and common GBK mis-decodes.
    """
    pua_count = sum(1 for c in text if _is_pua(c))
    marker_count = sum(1 for c in text if c in MOJIBAKE_MARKERS)

    if pua_count > 0 or marker_count > 5:
        # Report only: for clinical documents, manual intervention is preferred over
        # lossy automatic re-decoding, so the text is returned unchanged for review.
        logger.warning(
            "Mojibake detected: PUA=%d, markers=%d - returning text unchanged for manual review",
            pua_count, marker_count,
        )

    return text

def normalize_whitespace(text: str) -> str:
    """Normalize tabs, spaces, and newlines."""
    text = re.sub(r"[ \\t]+", " ", text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()

__all__ = ["detect_encoding", "fix_mojibake", "normalize_whitespace"]
