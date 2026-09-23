"""Ingestion stage: readers for various document formats."""

from .docx_reader import extract_docx_tables, extract_docx_text
from .pdf_reader import extract_pdf_tables, extract_pdf_text
from .pptx_reader import extract_pptx_notes, extract_pptx_text
from .xlsx_reader import extract_xlsx_data

__all__ = [
    "extract_pdf_text",
    "extract_pdf_tables",
    "extract_docx_text",
    "extract_docx_tables",
    "extract_xlsx_data",
    "extract_pptx_text",
    "extract_pptx_notes",
]
