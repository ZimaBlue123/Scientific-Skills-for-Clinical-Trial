"""Extract stage: table parsing and text normalization."""

from .extract_docx_tracked_text import extract_tracked_docx
from .table_extractor import find_tables_by_heading, parse_table_columns
from .text_normalizer import detect_encoding, fix_mojibake, normalize_whitespace

__all__ = [
    "extract_tracked_docx",
    "find_tables_by_heading",
    "parse_table_columns",
    "detect_encoding",
    "fix_mojibake",
    "normalize_whitespace",
]
