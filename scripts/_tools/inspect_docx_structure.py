"""Dump paragraph and table structure of a .docx (index, run count, preview text) for targeted inspection.

Usage:
    python scripts/_tools/inspect_docx_structure.py <file.docx>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx import Document


def inspect_docx_structure(path: Path | str, max_chars: int = 160) -> None:
    """Print indexed paragraph and table row structure for ``path``."""
    target = Path(path).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"DOCX file not found: {target}")
    doc = Document(str(target))
    print(f"== paragraphs: {len(doc.paragraphs)}  tables: {len(doc.tables)}")
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if not txt:
            continue
        runs = len(p.runs)
        print(f"[P{i:03d}] r{runs} | {txt[:max_chars]}")
    for ti, t in enumerate(doc.tables):
        print(f"== TABLE {ti} rows={len(t.rows)} cols={len(t.columns)}")
        for ri, row in enumerate(t.rows):
            cells = [c.text.strip().replace("\n", "/") for c in row.cells]
            print(f"  [T{ti}R{ri}] " + " | ".join(cells)[: max_chars + 40])


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Dump paragraph and table structure of a .docx (index + run count + text)."
    )
    ap.add_argument("docx", help="Path to target .docx file")
    ap.add_argument("--max-chars", type=int, default=160, help="Max preview characters per paragraph")
    args = ap.parse_args()
    try:
        inspect_docx_structure(args.docx, max_chars=args.max_chars)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
