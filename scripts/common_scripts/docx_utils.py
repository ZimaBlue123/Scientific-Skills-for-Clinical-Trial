# -*- coding: utf-8 -*-
"""
Common utilities for docx generation scripts.
Extracts shared functions from multiple generate_*.py scripts.
"""
from __future__ import annotations

from docx import Document
from docx.oxml.ns import qn


def apply_cn_en_fonts(doc: Document) -> None:
    """
    Enforce document-wide fonts:
    - Chinese (East Asia): 宋体
    - English (ASCII/HAnsi): Times New Roman
    
    Usage:
        from common_scripts.docx_utils import apply_cn_en_fonts
        apply_cn_en_fonts(doc)
    """
    def set_style(style_name: str) -> None:
        if style_name not in doc.styles:
            return
        style = doc.styles[style_name]
        font = style.font
        font.name = "Times New Roman"
        # East Asia font mapping (Chinese)
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:ascii"), "Times New Roman")
        rfonts.set(qn("w:hAnsi"), "Times New Roman")
        rfonts.set(qn("w:eastAsia"), "宋体")
        rfonts.set(qn("w:cs"), "Times New Roman")

    # Core styles that typically cover body/headings/tables.
    for name in [
        "Normal",
        "Title",
        "Heading 1",
        "Heading 2",
        "Heading 3",
        "Table Grid",
    ]:
        set_style(name)


# Backward compatibility alias
_apply_cn_en_fonts = apply_cn_en_fonts


__all__ = ["apply_cn_en_fonts", "_apply_cn_en_fonts"]