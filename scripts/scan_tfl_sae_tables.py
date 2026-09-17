#!/usr/bin/env python3
"""
scan_tfl_sae_tables.py

Locate SAE-related tables inside the Phase 1 / Phase 2 TFL docx volumes.

For every .docx under review_materials/统计/TFL-Phase*, walk the document body in
order (paragraphs + tables). For each table, record:
  * its index
  * the nearest preceding heading / paragraph text (TFL listing title)
  * the first two rows (usually the column header + first data row)

Only tables whose title or header text mentions SAE / 严重不良事件 / 相关性 are
written to the report, plus a short "ALL TABLE TITLES" index so nothing gets
missed.

Usage:
    python scripts/scan_tfl_sae_tables.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
STAT_DIR = ROOT / "review_materials" / "统计"
OUT_PATH = ROOT / "output" / "tfl_sae_table_scan.txt"

SAE_KEYWORDS = ("SAE", "严重不良事件", "严重不良", "相关性")


def iter_block_items(parent):
    """Yield (kind, object) in document order."""
    from docx.document import Document as _Doc

    parent_elm = parent.element.body if isinstance(parent, _Doc) else parent._element
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield ("p", Paragraph(child, parent))
        elif isinstance(child, CT_Tbl):
            yield ("t", Table(child, parent))


def cell_text(cell) -> str:
    return re.sub(r"\s+", " ", cell.text).strip()


def row_texts(table: Table, idx: int) -> list[str]:
    if idx >= len(table.rows):
        return []
    seen = []
    for cell in table.rows[idx].cells:
        t = cell_text(cell)
        if not seen or seen[-1] != t:  # collapse merged duplicates
            seen.append(t)
    return seen


def scan_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (hits, index_lines)."""
    doc = Document(str(path))
    hits: list[str] = []
    index_lines: list[str] = []

    last_title = ""
    t_idx = 0
    for kind, obj in iter_block_items(doc):
        if kind == "p":
            txt = obj.text.strip()
            if txt:
                last_title = txt
            continue

        t_idx += 1
        header = row_texts(obj, 0)
        first = row_texts(obj, 1) if len(obj.rows) > 1 else []
        head_blob = " ".join(header)
        idx_line = f"  [T{t_idx:02d}] rows={len(obj.rows)} cols={len(obj.columns)} | title: {last_title[:120]}"
        index_lines.append(idx_line)
        index_lines.append(f"        header: {head_blob[:400]}")

        blob = f"{last_title} {head_blob}"
        if any(k in blob for k in SAE_KEYWORDS):
            hits.append(f"\n--- {path.name}  TABLE #{t_idx} (rows={len(obj.rows)}) ---")
            hits.append(f"TITLE : {last_title}")
            hits.append(f"HEADER: {' | '.join(header)}")
            if first:
                hits.append(f"ROW1  : {' | '.join(first)}")
            for r in range(2, min(len(obj.rows), 5)):
                hits.append(f"ROW{r}  : {' | '.join(row_texts(obj, r))}")
    return hits, index_lines


def main() -> int:
    files = sorted([p for d in ("TFL-Phase1", "TFL-Phase2") for p in (STAT_DIR / d).glob("*.docx")])
    if not files:
        print(f"no docx found under {STAT_DIR}")
        return 1

    out: list[str] = ["# SAE table scan report", ""]
    all_hits: list[str] = []
    all_index: list[str] = []

    for f in files:
        print(f"scanning {f.name} ...", file=sys.stderr)
        hits, index_lines = scan_file(f)
        all_index.append(f"\n===== {f.name} =====")
        all_index.extend(index_lines)
        if hits:
            all_hits.append(f"\n########## {f.name} ##########")
            all_hits.extend(hits)

    out.append("#" * 100)
    out.append("# PART 1 - TABLES MATCHING SAE KEYWORDS")
    out.append("#" * 100)
    out.extend(all_hits or ["(no hits)"])
    out.append("")
    out.append("#" * 100)
    out.append("# PART 2 - FULL TABLE INDEX (all tables, all files)")
    out.append("#" * 100)
    out.extend(all_index)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(out), encoding="utf-8")
    print(f"OK -> {OUT_PATH} ({len(chr(10).join(out)):,} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
