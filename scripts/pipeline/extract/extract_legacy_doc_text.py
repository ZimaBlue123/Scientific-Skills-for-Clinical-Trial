"""Extract plain text and table text from legacy binary .doc files via Word COM.

For each ``*.doc`` in ``<src_dir>`` (or a single ``.doc`` file), writes two UTF-8 files to ``<out_dir>``:
    - ``<stem>.txt``        : full document text (paragraph text, newline separated)
    - ``<stem>.tables.txt`` : every table dumped as TAB-separated rows

Usage:
    python scripts/pipeline/extract/extract_legacy_doc_text.py <src_dir_or_file> <out_dir>
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def extract_one_doc(word_app, doc_path: Path, out_dir: Path) -> None:
    """Extract paragraph text and tables from a single legacy .doc file."""
    stem = doc_path.stem
    doc = word_app.Documents.Open(str(doc_path.resolve()), ReadOnly=True)
    try:
        text = doc.Content.Text
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        (out_dir / f"{stem}.txt").write_text(text, encoding="utf-8")

        tables_txt: list[str] = []
        for ti in range(1, doc.Tables.Count + 1):
            tbl = doc.Tables(ti)
            tables_txt.append(f"=== TABLE {ti} ({tbl.Rows.Count} rows) ===")
            for ri in range(1, tbl.Rows.Count + 1):
                cells: list[str] = []
                for ci in range(1, tbl.Columns.Count + 1):
                    try:
                        raw = tbl.Cell(ri, ci).Range.Text
                    except Exception:
                        raw = ""
                    raw = raw.replace("\r\n", " ").replace("\r", " ").replace("\x07", "")
                    cells.append(" ".join(raw.split()))
                tables_txt.append("\t".join(cells))
            tables_txt.append("")
        (out_dir / f"{stem}.tables.txt").write_text("\n".join(tables_txt), encoding="utf-8")
        print(f"OK  {stem}  chars={len(text)} tables={doc.Tables.Count}")
    finally:
        doc.Close(False)


def extract_legacy_docs(src: Path | str, out_dir: Path | str) -> int:
    """Batch extract legacy .doc files into ``out_dir`` using Word COM."""
    try:
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError("pywin32 is required for legacy .doc COM extraction.") from exc

    src_path = Path(src)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    files = [src_path] if src_path.is_file() else sorted(src_path.glob("*.doc"))
    if not files:
        print(f"No .doc files found in {src_path}", file=sys.stderr)
        return 1

    app = win32.Dispatch("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        for f in files:
            extract_one_doc(app, f, out_path)
    finally:
        app.Quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract plain text and tables from legacy .doc files via Word COM."
    )
    parser.add_argument("src", help="Source directory containing .doc files or a single .doc file")
    parser.add_argument("out_dir", help="Output directory for .txt and .tables.txt files")
    args = parser.parse_args()
    return extract_legacy_docs(args.src, args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["extract_one_doc", "extract_legacy_docs"]
