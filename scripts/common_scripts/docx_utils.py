# -*- coding: utf-8 -*-
"""
Common utilities for docx generation scripts.

Shared by multiple ``generate_*.py`` scripts in this directory. Importing
this module from a script living in ``scripts/`` requires adding the
``scripts/`` folder to ``sys.path`` (the existing project scripts use
``sys.path.insert(0, os.path.dirname(__file__))`` for that purpose).

Usage
-----
    from common_scripts.docx_utils import apply_cn_en_fonts
    apply_cn_en_fonts(doc)
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from docx import Document
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

# (ascii / hAnsi / eastAsia / cs) font names applied to every style below.
_ASCII_FONT = "Times New Roman"
_EAST_ASIA_FONT = "宋体"

# Core styles that typically cover body / headings / tables in a docx.
_TARGET_STYLES: tuple[str, ...] = (
    "Normal",
    "Title",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Table Grid",
)


def _set_style_fonts(doc: Document, style_name: str) -> bool:
    """Apply the CN/EN font mapping to a single style.

    Returns ``True`` if the style was found and updated, ``False`` if it
    was missing from the document (some style names are not always present).
    """
    if style_name not in doc.styles:
        return False
    style = doc.styles[style_name]
    font = style.font
    font.name = _ASCII_FONT

    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), _ASCII_FONT)
    rfonts.set(qn("w:hAnsi"), _ASCII_FONT)
    rfonts.set(qn("w:eastAsia"), _EAST_ASIA_FONT)
    rfonts.set(qn("w:cs"), _ASCII_FONT)
    return True


def apply_cn_en_fonts(
    doc: Document,
    styles: Optional[Iterable[str]] = None,
) -> int:
    """Enforce document-wide fonts:

    - English (ASCII / hAnsi / cs): Times New Roman
    - Chinese (eastAsia): 宋体

    Parameters
    ----------
    doc:
        The python-docx ``Document`` to mutate in place.
    styles:
        Optional iterable of style names to override. Defaults to the
        project-wide constant ``_TARGET_STYLES``.

    Returns
    -------
    int
        The number of styles that were actually found and updated.
    """
    target_styles: Iterable[str] = list(styles) if styles is not None else _TARGET_STYLES
    updated = 0
    for name in target_styles:
        if _set_style_fonts(doc, name):
            updated += 1
        else:
            logger.debug("style not present, skipping: %s", name)
    return updated


# Backward compatibility alias.
_apply_cn_en_fonts = apply_cn_en_fonts


__all__ = ["apply_cn_en_fonts", "_apply_cn_en_fonts"]
