"""Update Word (.docx) Table of Contents (TOC) and page number fields via Word COM.

Usage:
    python scripts/pipeline/export/update_docx_toc_fields.py <file.docx>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def update_docx_toc_fields(docx_path: Path | str) -> tuple[int, int]:
    """Update all fields and TOCs in ``docx_path`` via Word COM and return ``(toc_count, page_count)``."""
    try:
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError("pywin32 is required to update Word TOC fields via COM.") from exc

    target = Path(docx_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"DOCX file not found: {target}")

    app = win32.Dispatch("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    doc = None
    try:
        doc = app.Documents.Open(str(target))
        doc.Fields.Update()
        toc_count = doc.TablesOfContents.Count
        for idx in range(1, toc_count + 1):
            doc.TablesOfContents(idx).Update()
        doc.Repaginate()
        if toc_count > 0:
            doc.TablesOfContents(1).Update()
        doc.Save()
        pages = int(doc.ComputeStatistics(2))
        return toc_count, pages
    finally:
        if doc is not None:
            doc.Close(0)
        app.Quit()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update Word (.docx) TOC and page number fields in-place via Word COM."
    )
    parser.add_argument("docx_path", help="Path to target .docx file")
    args = parser.parse_args()

    try:
        toc_count, pages = update_docx_toc_fields(args.docx_path)
        print(f"Updated {toc_count} TOC field(s); total pages: {pages}")
        return 0
    except Exception as exc:
        print(f"Error updating TOC fields: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["update_docx_toc_fields"]
