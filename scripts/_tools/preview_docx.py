"""Render a .docx to PDF + PNG pages for visual QA.

Word is the only renderer that reproduces pagination exactly, so the preview goes
through Word COM (ExportAsFixedFormat) and then pymupdf for the page images.

Usage
-----
    python scripts/_tools/preview_docx.py report.docx -o out_dir
    python scripts/_tools/preview_docx.py report.docx -o out_dir --dpi 150

Outputs ``<out_dir>/<tag>.pdf`` and ``<out_dir>/<tag>_p<N>.png``.

Notes
-----
* Word resolves the export filename against its own working directory, so the
  target path is always resolved to an absolute one (same trap as preview_xlsx).
* Tag defaults to the file stem; a stem containing ``<`` or ``>`` is not a legal
  Windows filename, so pass ``-t`` explicitly in that case.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf
import win32com.client as win32

WD_FORMAT_PDF = 17


def export(docx_path: Path, out_dir: Path, tag: str, dpi: int) -> list[Path]:
    docx_path = Path(docx_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"{tag}.pdf"

    app = win32.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = False
    doc = None
    try:
        doc = app.Documents.Open(str(docx_path), ReadOnly=True)
        doc.ExportAsFixedFormat(str(pdf), WD_FORMAT_PDF)
    finally:
        if doc is not None:
            doc.Close(False)
        app.Quit()

    src = pymupdf.open(pdf)
    pages: list[Path] = []
    for i, page in enumerate(src):
        png = out_dir / f"{tag}_p{i + 1}.png"
        page.get_pixmap(dpi=dpi).save(png)
        pages.append(png)
    print(f"{tag}: {len(pages)} page(s) -> {out_dir}")
    return pages


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render docx to PDF/PNG via Word for layout QA")
    ap.add_argument("docx")
    ap.add_argument("-o", "--out-dir", default=None, help="default: <docx dir>/_preview")
    ap.add_argument("-t", "--tag", default=None, help="output file prefix")
    ap.add_argument("--dpi", type=int, default=120)
    args = ap.parse_args(argv)

    docx_path = Path(args.docx)
    if not docx_path.is_file():
        print(f"not found: {docx_path}", file=sys.stderr)
        return 1
    out_dir = Path(args.out_dir) if args.out_dir else docx_path.parent / "_preview"
    tag = args.tag or docx_path.stem.replace(" ", "_")
    export(docx_path, out_dir, tag, args.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
