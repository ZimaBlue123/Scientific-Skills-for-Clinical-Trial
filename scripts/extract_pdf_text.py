#!/usr/bin/env python3
"""Generic PDF text extractor (pypdf based).

Usage:
    python extract_pdf_text.py <input.pdf> [output.txt] [--max-pages N]
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path, max_pages: int | None = None) -> str:
    try:
        import pdf_inspector  # type: ignore

        result = pdf_inspector.process_pdf(str(pdf_path))
        if result.markdown and result.pdf_type not in ("scanned", "image_based"):
            return result.markdown.strip()
    except Exception:
        pass

    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    total = len(reader.pages)
    limit = total if max_pages is None else min(total, max_pages)
    for idx in range(limit):
        page = reader.pages[idx]
        try:
            txt = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            txt = f"<<extract error: {exc}>>"
        chunks.append(f"\n========= PAGE {idx + 1}/{total} =========\n{txt}")
    return "".join(chunks)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    pos = [a for a in argv[1:] if not a.startswith("--")]
    max_pages = None
    if "--max-pages" in argv:
        max_pages = int(argv[argv.index("--max-pages") + 1])
        pos = [p for p in pos if p != str(max_pages)]

    src = Path(pos[0])
    text = extract_pdf_text(src, max_pages)

    if len(pos) > 1:
        out = Path(pos[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out} ({len(text)} chars)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
