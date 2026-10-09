"""Convert legacy binary .doc files to .docx using Microsoft Word COM.

Constraint (workspace policy): this script must live under ``scripts/``.

Why not python-docx: it can only read the OOXML .docx container, while legacy
``.doc`` files are OLE2 (magic ``d0 cf 11 e0``) Compound Files. Word COM is the
only lossless path on Windows.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Word SaveAs2 format enum: wdFormatXMLDocument (macro-free .docx) = 12
WD_FORMAT_XML_DOCUMENT = 12
# Suppress the "file is being converted" / save-changes dialogs
WD_ALERT_NONE = 0


def convert_doc_to_docx(src: Path, dst: Path | None = None) -> Path:
    """Convert a single .doc file to .docx. Returns the produced path."""
    import win32com.client as win32

    src = Path(src).resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    dst = Path(dst).resolve() if dst else src.with_suffix(".docx")

    word = win32.gencache.EnsureDispatch("Word.Application")
    try:
        word.Visible = False
        word.DisplayAlerts = WD_ALERT_NONE
        doc = word.Documents.Open(str(src), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.SaveAs2(str(dst), FileFormat=WD_FORMAT_XML_DOCUMENT)
        finally:
            doc.Close(SaveChanges=False)
    finally:
        word.Quit()

    if not dst.exists():
        raise RuntimeError(f"Word did not produce output: {dst}")
    return dst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Convert .doc -> .docx via Word COM")
    ap.add_argument("src", nargs="+", help="Source .doc file(s)")
    ap.add_argument("-o", "--output", help="Output path (single source only)")
    args = ap.parse_args(argv)

    if args.output and len(args.src) > 1:
        ap.error("--output can only be used with a single source file")

    for s in args.src:
        src = Path(s)
        try:
            out = convert_doc_to_docx(src, Path(args.output) if args.output else None)
            print(f"OK   {src.name} -> {out}")
        except Exception as exc:  # noqa: BLE001 - report per file, keep batch going
            print(f"FAIL {src.name}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
