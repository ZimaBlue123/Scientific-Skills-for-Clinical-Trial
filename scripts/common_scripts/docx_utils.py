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
from collections.abc import Iterable
from pathlib import Path

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
    styles = getattr(doc, "styles", None)
    if styles is None:
        logger.warning("document object exposes no .styles; aborting font update")
        return False
    if style_name not in styles:
        return False
    try:
        style = styles[style_name]
    except (KeyError, ValueError):
        logger.debug("style lookup failed despite membership check: %s", style_name)
        return False
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
    styles: Iterable[str] | None = None,
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





# -----------------------------------------------------------------------------
# Legacy .doc -> .docx conversion (Windows-only, formerly scripts/convert_doc_to_docx.py)
# -----------------------------------------------------------------------------
def convert_doc_to_docx(input_path, output_path=None):
    """Convert a legacy Word ``.doc`` file to ``.docx`` via Word COM.

    Windows-only. Requires ``pywin32``. Returns the output path as a
    ``pathlib.Path``. On Linux/macOS returns ``None`` and logs an error.

    Parameters
    ----------
    input_path : str | os.PathLike
        Path to the input ``.doc`` file.
    output_path : str | os.PathLike | None
        Target ``.docx`` path. If ``None`` the helper writes alongside
        the input file with the same stem.
    """
    try:
        import os as _os

        import pythoncom  # type: ignore[import-not-found]
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        logger.error(
            "convert_doc_to_docx requires pywin32 on Windows; "
            "module unavailable in this environment."
        )
        return None

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        try:
            word = win32com.client.Dispatch("Word.Application")
        except Exception as exc:  # noqa: BLE001
            logger.error("failed to launch Word.Application: %s", exc)
            return None
        word.Visible = False
        if output_path is None:
            output_path = _os.path.splitext(str(input_path))[0] + ".docx"
        try:
            doc = word.Documents.Open(_os.path.abspath(str(input_path)))
            doc.SaveAs(_os.path.abspath(str(output_path)), 16)  # 16 = wdFormatXMLDocument
        except Exception as exc:  # noqa: BLE001
            logger.error("COM error converting %s: %s", input_path, exc)
            return None
        finally:
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:  # noqa: BLE001
                    logger.debug("doc.Close raised", exc_info=True)
        return Path(str(output_path))
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:  # noqa: BLE001
                logger.debug("word.Quit raised", exc_info=True)
        try:
            pythoncom.CoUninitialize()
        except Exception:  # noqa: BLE001
            logger.debug("pythoncom.CoUninitialize raised", exc_info=True)


__all__ = [
    "apply_cn_en_fonts",
    "_apply_cn_en_fonts",
    "convert_doc_to_docx",
]
