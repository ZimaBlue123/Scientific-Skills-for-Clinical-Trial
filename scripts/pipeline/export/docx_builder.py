"""DOCX export utilities."""

from __future__ import annotations

import logging
import re
import zipfile
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)

_ASCII_FONT = "Times New Roman"
_EAST_ASIA_FONT = "宋体"
_TARGET_STYLES = (
    "Normal",
    "Title",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Table Grid",
)


def apply_cn_en_fonts(doc, styles: Iterable[str] | None = None) -> int:
    """Enforce document-wide fonts: Times New Roman for English, 宋体 for Chinese."""
    from docx.oxml.ns import qn

    target_styles = list(styles) if styles is not None else _TARGET_STYLES
    updated = 0

    styles_dict = getattr(doc, "styles", None)
    if styles_dict is None:
        return 0

    for style_name in target_styles:
        if style_name not in styles_dict:
            continue
        try:
            style = styles_dict[style_name]
            font = style.font
            font.name = _ASCII_FONT

            rpr = style.element.get_or_add_rPr()
            rfonts = rpr.get_or_add_rFonts()
            rfonts.set(qn("w:ascii"), _ASCII_FONT)
            rfonts.set(qn("w:hAnsi"), _ASCII_FONT)
            rfonts.set(qn("w:eastAsia"), _EAST_ASIA_FONT)
            rfonts.set(qn("w:cs"), _ASCII_FONT)
            updated += 1
        except (KeyError, ValueError):
            # Styles that expose no rPr/rFonts element cannot be patched; skip quietly
            # but keep a trace so silent font regressions stay diagnosable.
            logger.debug("Skipping font patch for style %r: no rPr/rFonts element", style_name)

    return updated


def create_clinical_docx(output_path: Path | str, content: str) -> None:
    """Create a basic clinical DOCX report with standard fonts."""
    from docx import Document

    doc = Document()
    apply_cn_en_fonts(doc)

    for line in content.split("\n"):
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        else:
            doc.add_paragraph(line)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    logger.info(f"Created DOCX at {out}")


_COMMENT_PARTS = (
    "word/comments.xml",
    "word/commentsExtended.xml",
    "word/commentsIds.xml",
    "word/people.xml",
)
_COMMENT_RUN_RE = re.compile(
    r"<w:r(?:\s[^>]*)?>(?:(?!</w:r>).)*?<w:commentReference[^>]*/>(?:(?!</w:r>).)*?</w:r>",
    re.S,
)


def strip_docx_comments(src_path: Path | str, out_path: Path | str | None = None) -> int:
    """Remove all comment parts and in-body comment range markers at the OOXML string level.

    Operates on raw XML text rather than ElementTree round-tripping so original namespace
    prefixes (e.g. ``w14``, ``w15``, ``wp14`` referenced by ``mc:Ignorable``) remain intact.
    Returns the total number of ``<w:commentReference>`` runs stripped.
    """
    src = Path(src_path)
    dst = Path(out_path) if out_path is not None else src
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    drop = {n for n in names if n in _COMMENT_PARTS}
    removed_runs = 0

    for part in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml"):
        if part not in data:
            continue
        xml = data[part].decode("utf-8")
        removed_runs += len(_COMMENT_RUN_RE.findall(xml))
        xml = _COMMENT_RUN_RE.sub("", xml)
        xml = re.sub(r"<w:commentRangeStart[^>]*/>", "", xml)
        xml = re.sub(r"<w:commentRangeEnd[^>]*/>", "", xml)
        data[part] = xml.encode("utf-8")

    rels = "word/_rels/document.xml.rels"
    if rels in data:
        xml = data[rels].decode("utf-8")
        data[rels] = re.sub(
            r"<Relationship\b[^>]*/>",
            lambda m: "" if re.search(r"(comments|people)", m.group(0), re.I) else m.group(0),
            xml,
        ).encode("utf-8")

    ct = "[Content_Types].xml"
    if ct in data:
        xml = data[ct].decode("utf-8")
        data[ct] = re.sub(
            r"<Override\b[^>]*/>",
            lambda m: (
                ""
                if re.search(
                    r"/word/(comments|commentsExtended|commentsIds|people)\.xml",
                    m.group(0),
                    re.I,
                )
                else m.group(0)
            ),
            xml,
        ).encode("utf-8")

    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        ordered = ["[Content_Types].xml"] + [x for x in data if x != "[Content_Types].xml"]
        for n in ordered:
            if n in drop or n not in data:
                continue
            zout.writestr(n, data[n])

    return removed_runs


__all__ = ["create_clinical_docx", "apply_cn_en_fonts", "strip_docx_comments"]
