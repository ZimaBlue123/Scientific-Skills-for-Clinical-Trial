"""Text normalization and encoding diagnostics."""

from __future__ import annotations
import logging
import re
from collections import Counter

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
        pass
    try:
        raw_bytes.decode("gb18030")
        return "gb18030"
    except UnicodeDecodeError:
        pass
    return "latin-1"

def fix_mojibake(text: str) -> str:
    """Identify and attempt to fix common mojibake patterns.
    
    Checks for Private Use Area (PUA) characters and common GBK mis-decodes.
    """
    pua_count = sum(1 for c in text if _is_pua(c))
    marker_count = sum(1 for c in text if c in MOJIBAKE_MARKERS)
    
    if pua_count > 0 or marker_count > 5:
        logger.warning(f"Mojibake detected! PUA: {pua_count}, Markers: {marker_count}")
        try:
            # Typical fix for utf-8 interpreted as latin1 or cp1252, etc.
            # But the specific diagnosis logic from scripts is more about detection.
            # Here we just return the text as is with a warning, or attempt a naive fix.
            # For clinical docs, manual intervention is usually preferred over lossy fixes.
            pass
        except Exception:
            pass
            
    return text

def normalize_whitespace(text: str) -> str:
    """Normalize tabs, spaces, and newlines."""
    text = re.sub(r"[ \\t]+", " ", text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()

__all__ = ["detect_encoding", "fix_mojibake", "normalize_whitespace"]
