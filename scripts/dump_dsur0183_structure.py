#!/usr/bin/env python3
"""Dump DSUR#2 draft (converted docx) paragraphs + tables as JSON lines.

Produces review_materials/018-3/_work/dsur_structure.jsonl with one record per
paragraph / table so an auditor can diff paragraph texts against tables.
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document  # type: ignore
from docx.oxml.table import CT_Tbl  # type: ignore
from docx.oxml.text.paragraph import CT_P  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = ROOT / "review_materials" / "018-3" / "_work"
DOCX = WORK_DIR / "dsur_input.docx"
OUT = WORK_DIR / "dsur_structure.jsonl"


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield ("p", child)
        elif isinstance(child, CT_Tbl):
            yield ("t", child)


def main() -> int:
    if not DOCX.exists():
        print(f"docx missing: {DOCX}")
        return 2
    doc = Document(str(DOCX))
    records = []
    idx_p = 0
    idx_t = 0
    for kind, child in iter_block_items(doc):
        if kind == "p":
            from docx.text.paragraph import Paragraph  # type: ignore

            para = Paragraph(child, doc)
            idx_p += 1
            text = para.text.strip()
            if not text:
                continue
            records.append({"type": "p", "id": f"P{idx_p}", "style": para.style.name, "text": text})
        else:
            from docx.table import Table  # type: ignore

            table = Table(child, doc)
            idx_t += 1
            rows = []
            for r in table.rows:
                cells = [c.text.strip().replace("\n", " / ") for c in r.cells]
                rows.append(cells)
            records.append({"type": "t", "id": f"T{idx_t}", "rows": rows})
    OUT.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8"
    )
    print(f"wrote {len(records)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
