#!/usr/bin/env python
"""Batch-extract text from a review-materials tree into a parallel .txt tree.

Usage:
    python scripts/pipeline/extract/batch_extract_materials.py <src_dir> <out_dir>

Supports .docx (paragraphs + tables in body order), .pptx (slide text, tables,
speaker notes, chart series data), .xlsx (all sheets), .pdf (per-page text with
page markers). Each source file maps to <out_dir>/<relative_path>.txt.
A per-file manifest (size, chars, status) is printed as tab-separated lines.

No hardcoded paths; safe to reuse for any materials folder.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

SUPPORTED = {".docx", ".pptx", ".xlsx", ".pdf"}


def _docx_text(path: Path) -> str:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    out = []
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            p = Paragraph(child, doc)
            txt = p.text.strip()
            if txt:
                style = ""
                try:
                    style = p.style.name or ""
                except (AttributeError, KeyError, ValueError):
                    style = ""  # paragraph with an unresolved / missing style id
                if style.lower().startswith("heading") or style.lower().startswith("title"):
                    out.append(f"## [{style}] {txt}")
                else:
                    out.append(txt)
        elif child.tag == qn("w:tbl"):
            t = Table(child, doc)
            out.append("[TABLE]")
            for row in t.rows:
                cells = []
                seen = set()
                for c in row.cells:
                    if id(c._tc) in seen:
                        continue
                    seen.add(id(c._tc))
                    cells.append(" ".join(c.text.split()))
                out.append(" | ".join(cells))
            out.append("[/TABLE]")
    return "\n".join(out)


def _pptx_text(path: Path) -> str:
    from pptx import Presentation

    prs = Presentation(str(path))
    out = []

    def walk_shapes(shapes, depth=0):
        for sh in shapes:
            if sh.shape_type == 6:  # GROUP
                out.append(f"[GROUP depth={depth}]")
                walk_shapes(sh.shapes, depth + 1)
                continue
            if sh.has_text_frame:
                t = " ".join(sh.text_frame.text.split())
                if t:
                    out.append(t)
            if getattr(sh, "has_table", False):
                out.append("[TABLE]")
                for row in sh.table.rows:
                    out.append(" | ".join(" ".join(c.text.split()) for c in row.cells))
                out.append("[/TABLE]")
            if getattr(sh, "has_chart", False):
                try:
                    ch = sh.chart
                    out.append("[CHART]")
                    cats = []
                    try:
                        cats = [str(c) for c in ch.plots[0].categories]
                    except (IndexError, AttributeError, KeyError, ValueError):
                        out.append("[CHART_CATEGORIES_UNREADABLE]")
                    if cats:
                        out.append("CATEGORIES: " + " | ".join(cats))
                    for s in ch.series:
                        vals = []
                        try:
                            vals = ["" if v is None else str(v) for v in s.values]
                        except (AttributeError, KeyError, ValueError, TypeError):
                            vals = ["<unreadable>"]
                        out.append(f"SERIES {s.name}: " + " | ".join(vals))
                    out.append("[/CHART]")
                except Exception as exc:  # malformed chart part: keep extracting the rest
                    out.append(f"[CHART_ERROR] {type(exc).__name__}: {exc}")

    for i, slide in enumerate(prs.slides, 1):
        out.append(f"### SLIDE {i}")
        walk_shapes(slide.shapes)
        try:
            if slide.has_notes_slide:
                nt = " ".join(slide.notes_slide.notes_text_frame.text.split())
                if nt:
                    out.append(f"[NOTES] {nt}")
        except (AttributeError, KeyError) as exc:
            out.append(f"[NOTES_ERROR] {type(exc).__name__}: {exc}")
    return "\n".join(out)


def _xlsx_text(path: Path) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"### SHEET {ws.title}  dims={ws.max_row}x{ws.max_column}")
        for row in ws.iter_rows(values_only=True):
            vals = ["" if v is None else str(v) for v in row]
            if any(v.strip() for v in vals):
                out.append(" | ".join(vals))
    wb.close()
    return "\n".join(out)


def _pdf_text(path: Path) -> str:
    import fitz

    doc = fitz.open(str(path))
    out = [f"[PDF_PAGES] {len(doc)}"]
    for i, page in enumerate(doc, 1):
        txt = page.get_text("text")
        out.append(f"### PAGE {i}")
        out.append(txt.strip())
    doc.close()
    return "\n".join(out)


EXTRACTORS = {
    ".docx": _docx_text,
    ".pptx": _pptx_text,
    ".xlsx": _xlsx_text,
    ".pdf": _pdf_text,
}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: batch_extract_materials.py <src_dir> <out_dir>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1]).resolve()
    outdir = Path(sys.argv[2]).resolve()
    if not src.is_dir():
        print(f"src not a dir: {src}", file=sys.stderr)
        return 2
    outdir.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
    print("STATUS\tRELPATH\tSIZE_KB\tCHARS")
    for p in files:
        rel = p.relative_to(src)
        dst = outdir / (str(rel) + ".txt")
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = EXTRACTORS[p.suffix.lower()](p)
            dst.write_text(text, encoding="utf-8")
            print(f"OK\t{rel}\t{p.stat().st_size // 1024}\t{len(text)}")
        except Exception as e:
            dst.write_text(f"[EXTRACT_ERROR] {type(e).__name__}: {e}\n{traceback.format_exc()}", encoding="utf-8")
            print(f"ERR\t{rel}\t{p.stat().st_size // 1024}\t0\t{type(e).__name__}: {e}")
    skipped = [p.relative_to(src) for p in src.rglob("*") if p.is_file() and p.suffix.lower() not in SUPPORTED]
    if skipped:
        print(f"\nSKIPPED_UNSUPPORTED ({len(skipped)}):")
        for s in skipped:
            print(f"  {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
