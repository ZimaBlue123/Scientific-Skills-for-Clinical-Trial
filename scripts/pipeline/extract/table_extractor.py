"""Table extraction utilities."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def find_tables_by_heading(tables: list[list[list[str]]], heading_keywords: list[str]) -> list[list[list[str]]]:
    """Find tables that contain specific heading keywords."""
    matched_tables = []

    for table in tables:
        if not table:
            continue
        header_row = " ".join(table[0]).lower()
        if all(kw.lower() in header_row for kw in heading_keywords):
            matched_tables.append(table)

    return matched_tables

def parse_table_columns(table: list[list[str]], column_indices: list[int]) -> list[list[str]]:
    """Extract specific columns from a table."""
    parsed = []

    for row in table:
        parsed_row = []
        for idx in column_indices:
            if idx < len(row):
                parsed_row.append(row[idx])
            else:
                parsed_row.append("")
        parsed.append(parsed_row)

    return parsed

__all__ = ["find_tables_by_heading", "parse_table_columns"]
