"""PDF extraction module."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_pdf_text(pdf_path: Path | str, max_pages: int | None = None) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader

    path = Path(pdf_path)
    reader = PdfReader(str(path))
    chunks: list[str] = []
    total = len(reader.pages)
    limit = total if max_pages is None else min(total, max_pages)

    for idx in range(limit):
        page = reader.pages[idx]
        try:
            txt = page.extract_text() or ""
        except Exception as exc:
            txt = f"<<extract error: {exc}>>"
        chunks.append(f"\\n========= PAGE {idx + 1}/{total} =========\\n{txt}")
    return "".join(chunks)

def extract_pdf_tables(pdf_path: Path | str) -> list[list[list[str]]]:
    """Extract tables from a PDF."""
    # Placeholder for table extraction logic
    return []

__all__ = ["extract_pdf_text", "extract_pdf_tables"]
