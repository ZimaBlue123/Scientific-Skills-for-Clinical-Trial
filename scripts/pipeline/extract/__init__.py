"""Extract stage: table parsing and text normalization."""

from .table_extractor import find_tables_by_heading, parse_table_columns
from .text_normalizer import detect_encoding, fix_mojibake, normalize_whitespace

__all__ = [
    "find_tables_by_heading",
    "parse_table_columns",
    "detect_encoding",
    "fix_mojibake",
    "normalize_whitespace",
]
