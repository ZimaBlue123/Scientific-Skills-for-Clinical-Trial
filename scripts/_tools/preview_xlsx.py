"""Render an .xlsx to PDF + PNG pages for visual QA of the print layout.

Excel is the only renderer that honours page setup (fit-to-width, manual row
breaks, floating charts), so the preview goes through Excel COM rather than
through openpyxl/pandas.

Usage
-----
    # whole workbook
    python scripts/_tools/preview_xlsx.py book.xlsx -o out_dir

    # a single sheet (fast when a workbook has a wide listing sheet)
    python scripts/_tools/preview_xlsx.py book.xlsx -o out_dir -s "02_总体结果"

Outputs ``<out_dir>/<tag>.pdf`` and ``<out_dir>/<tag>_p<N>.png``.

Note: floating charts anchored in rows that sit *past* the last populated cell
are silently dropped from the print/export unless ``print_area`` covers them.
If a chart is missing from the preview, check the sheet's print area first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf
import win32com.client as win32


def export(xlsx: Path, out_dir: Path, sheet: str | None, tag: str, dpi: int) -> list[Path]:
    # Excel resolves the export filename against *its own* working directory,
    # which is not necessarily the caller's cwd, so always hand it an absolute
    # path (a relative one intermittently raises "无法保存该文档").
    xlsx = Path(xlsx).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"{tag}.pdf"

    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(xlsx), ReadOnly=True)
        wb.Activate()
        if sheet:
            # Worksheet-level ExportAsFixedFormat is flaky on Excel 2016/2019
            # ("无法保存该文档。该文档可能已被打开"): dropping the sibling sheets
            # and exporting the workbook is reliable, and the page setup of the
            # kept sheet is untouched by the deletions.
            for other in list(wb.Worksheets):
                if other.Name != sheet:
                    other.Delete()
        wb.ExportAsFixedFormat(0, str(pdf))
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        app.Quit()

    doc = pymupdf.open(pdf)
    pages: list[Path] = []
    for i, page in enumerate(doc):
        png = out_dir / f"{tag}_p{i + 1}.png"
        page.get_pixmap(dpi=dpi).save(png)
        pages.append(png)
    print(f"{tag}: {len(pages)} page(s) -> {out_dir}")
    return pages


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render xlsx to PDF/PNG via Excel for layout QA")
    ap.add_argument("xlsx")
    ap.add_argument("-o", "--out-dir", default=None, help="default: <xlsx dir>/_preview")
    ap.add_argument("-s", "--sheet", default=None, help="sheet name; omit for the whole workbook")
    ap.add_argument("-t", "--tag", default=None, help="output file prefix")
    ap.add_argument("--dpi", type=int, default=120)
    args = ap.parse_args(argv)

    xlsx = Path(args.xlsx).resolve()
    if not xlsx.is_file():
        print(f"not found: {xlsx}", file=sys.stderr)
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else xlsx.parent / "_preview"
    tag = args.tag or (args.sheet or xlsx.stem).replace(" ", "_")
    export(xlsx, out_dir, args.sheet, tag, args.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
