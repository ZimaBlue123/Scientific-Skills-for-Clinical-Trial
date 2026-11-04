# -*- coding: utf-8 -*-
"""用 Word COM 读取 docx 的页数 / 批注数 / 目录条目（只读，不改文件）。

用法: python scripts/_tools/inspect_docx_word_stats.py <file.docx> [--update-toc]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect Word (.docx) page count, comments, and TOC entries via COM.")
    ap.add_argument("path")
    ap.add_argument("--update-toc", action="store_true")
    ap.add_argument("--dump-toc", action="store_true")
    args = ap.parse_args()

    p = Path(args.path).resolve()
    if not p.is_file():
        print(f"File not found: {p}", file=sys.stderr)
        return 1
    import win32com.client as win32

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(
            str(p),
            ReadOnly=not args.update_toc,
            AddToRecentFiles=False,
            Visible=False,
        )
        if args.update_toc:
            for i in range(1, doc.TablesOfContents.Count + 1):
                doc.TablesOfContents(i).Update()
            doc.Fields.Update()
        pages = doc.ComputeStatistics(2)  # wdStatisticPages
        words = doc.ComputeStatistics(0)
        chars = doc.ComputeStatistics(3)
        print("FILE  :", p.name)
        print("PAGES :", pages)
        print("WORDS :", words, " CHARS:", chars)
        print("PARAS :", doc.Paragraphs.Count)
        print("TABLES:", doc.Tables.Count)
        try:
            print("COMMENTS:", doc.Comments.Count)
        except Exception as e:
            print("COMMENTS: n/a", e)
        if args.dump_toc:
            print("--- TOC entries ---")
            for i in range(1, doc.TablesOfContents.Count + 1):
                toc = doc.TablesOfContents(i)
                rng = toc.Range
                print(f"[TOC {i}] {rng.Paragraphs.Count} paragraphs")
                for k in range(1, rng.Paragraphs.Count + 1):
                    t = rng.Paragraphs(k).Range.Text.replace("\r", "").replace("\x07", "|")
                    print(f"   {k:02d}  {t}")
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        word.Quit()
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    raise SystemExit(main())
