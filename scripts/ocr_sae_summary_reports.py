#!/usr/bin/env python3
"""
ocr_sae_summary_reports.py

OCR the scanned SAE summary reports so the investigator's causality rationale
("相关性：...") can be merged into the SAE listing workbook.

Pages that already carry a text layer are copied directly; only image pages are
rendered and recognised with RapidOCR. Results are cached as UTF-8 text so
re-runs are cheap.

Usage:
    python scripts/ocr_sae_summary_reports.py [--dir <pdf folder> --out <cache folder>]

Defaults: 肥城现场 -> .workbuddy/sae_report_ocr
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import fitz  # pymupdf
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "review_materials" / "统计" / "远大乙肝Ⅱ期-肥城现场-SAE总结报告汇总"
DEFAULT_OUT = ROOT / ".workbuddy" / "sae_report_ocr"
DPI = 200
TEXT_LAYER_MIN_CHARS = 50


def safe_stem(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", Path(name).stem)


def process(pdf: Path, src_dir: Path, out_dir: Path, engine) -> None:
    # keep the subject sub-folder (e.g. G33/) in the cache name to avoid clashes
    rel = pdf.relative_to(src_dir)
    stem = str(rel)[: -len(pdf.suffix)].replace("\\", "__").replace("/", "__")
    dest = out_dir / (re.sub(r'[\\/:*?"<>|]+', "_", stem) + ".txt")
    if dest.exists() and dest.stat().st_size > 0:
        print(f"skip (cached): {dest.name}", file=sys.stderr)
        return
    doc = fitz.open(str(pdf))
    chunks: list[str] = []
    for i, page in enumerate(doc, start=1):
        raw = page.get_text() or ""
        if len(raw.strip()) >= TEXT_LAYER_MIN_CHARS:
            chunks.append(f"\n{'=' * 28} PAGE {i} {'=' * 28}\n" + raw.strip())
            print(f"  {pdf.name[:34]} p{i}/{doc.page_count} (text layer)", file=sys.stderr)
            continue
        pix = page.get_pixmap(dpi=DPI)
        result, _ = engine(pix.tobytes("png"))
        lines = [item[1] for item in (result or [])]
        chunks.append(f"\n{'=' * 28} PAGE {i} {'=' * 28}\n" + "\n".join(lines))
        print(f"  {pdf.name[:34]} p{i}/{doc.page_count}", file=sys.stderr)
    doc.close()
    dest.write_text("\n".join(chunks), encoding="utf-8")
    print(f"OK -> {dest.name}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(DEFAULT_SRC), help="folder containing the SAE report PDFs")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="OCR text cache folder")
    ap.add_argument("--glob", default="*.pdf", help="file pattern, e.g. '*总结报告*.pdf'")
    args = ap.parse_args()

    src = Path(args.dir)
    out = Path(args.out)
    if not src.exists():
        print(f"missing source dir: {src}", file=sys.stderr)
        return 2

    out.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()
    pdfs = sorted(src.rglob(args.glob))
    print(f"{len(pdfs)} pdfs -> {out}", file=sys.stderr)
    for pdf in pdfs:
        process(pdf, src, out, engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
