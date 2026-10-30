#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract plain text and table text from legacy .doc files via Word COM.

Usage:
    python extract_ctr_doc_text.py <src_dir> <out_dir>

For each *.doc in <src_dir>, two UTF-8 files are written to <out_dir>:
    <stem>.txt        - full document text (paragraph text, \n separated)
    <stem>.tables.txt - every table dumped as TAB separated rows

Why Word COM and not a parser: CTR exports are legacy .doc (Word 97-2003
binary). python-docx cannot read them, and no LibreOffice / antiword is
guaranteed on Windows. Word COM is the only lossless path, and it also keeps
the table structure that we need for 试验药/对照药 and 终点指标.

Requires: pip install pywin32  (system python; the project venv has no pip)
"""

from __future__ import annotations

import os
import sys
import glob
import win32com.client as win32


def extract_one(word_app, doc_path: str, out_dir: str) -> None:
    stem = os.path.splitext(os.path.basename(doc_path))[0]
    doc = word_app.Documents.Open(os.path.abspath(doc_path), ReadOnly=True)
    try:
        text = doc.Content.Text
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        with open(os.path.join(out_dir, stem + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(text)

        tables_txt = []
        for ti in range(1, doc.Tables.Count + 1):
            tbl = doc.Tables(ti)
            tables_txt.append("=== TABLE %d (%d rows) ===" % (ti, tbl.Rows.Count))
            for ri in range(1, tbl.Rows.Count + 1):
                cells = []
                for ci in range(1, tbl.Columns.Count + 1):
                    try:
                        raw = tbl.Cell(ri, ci).Range.Text
                    except Exception:
                        raw = ""
                    raw = raw.replace("\r\n", " ").replace("\r", " ").replace("\x07", "")
                    raw = " ".join(raw.split())
                    cells.append(raw)
                tables_txt.append("\t".join(cells))
            tables_txt.append("")
        with open(os.path.join(out_dir, stem + ".tables.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(tables_txt))
        print("OK  %s  chars=%d tables=%d" % (stem, len(text), doc.Tables.Count))
    finally:
        doc.Close(False)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src_dir, "*.doc")))
    if not files:
        print("no .doc found in", src_dir)
        return 1

    app = win32.Dispatch("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        for f in files:
            extract_one(app, f, out_dir)
    finally:
        app.Quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
