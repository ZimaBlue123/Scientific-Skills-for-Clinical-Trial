"""Extract plain text and tables from a .docx without external deps.

This module parses an Office Open XML (.docx) package using only the Python
standard library and returns the body content as plain text. Paragraphs are
separated by blank lines, table rows by ``" | "``, and trailing whitespace is
trimmed. It is the lowest-level text extractor used by the project and is
imported by both ``extract_docx_full.py`` (full extraction) and
``extract_docx_to_md.py`` (markdown conversion).

Notes
-----
The WordprocessingML namespace URI is intentionally hard-coded; misspelling
it (e.g. ``schemas.openformats.org``) silently produces empty output because
``xml.etree.ElementTree`` then fails to match ``w:body``.
"""

from __future__ import annotations

import logging
import re
import sys
import zipfile
from pathlib import Path
from typing import Final
from xml.etree import ElementTree as ET

logger: logging.Logger = logging.getLogger(__name__)

# Canonical OOXML namespace for WordprocessingML (ECMA-376 / ISO 29500).
W_NS: Final[str] = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _text_from_element(el: ET.Element) -> str:
    """Recursively concatenate visible text nodes under ``el``.

    ``w:t`` yields its text, ``w:tab`` becomes ``"\\t"``, and ``w:br`` / ``w:cr``
    become ``"\\n"``. ``None`` text payloads (e.g. empty runs) are skipped.
    """
    parts: list[str] = []
    for node in el.iter():
        tag = node.tag
        if tag == f"{W_NS}t":
            if node.text:
                parts.append(node.text)
        elif tag == f"{W_NS}tab":
            parts.append("\t")
        elif tag in (f"{W_NS}br", f"{W_NS}cr"):
            parts.append("\n")
    return "".join(parts)


def extract_docx(path: Path) -> str:
    """Extract human-readable text from a .docx file.

    Parameters
    ----------
    path:
        Path to a valid OOXML Word document.

    Returns
    -------
    str
        UTF-8 text with paragraphs separated by blank lines. Returns an empty
        string when the document has no ``w:body`` element (which indicates a
        malformed or non-Word OOXML package).

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    zipfile.BadZipFile
        If ``path`` is not a valid ZIP archive.
    KeyError
        If the archive does not contain ``word/document.xml``.
    ET.ParseError
        If ``word/document.xml`` is not well-formed XML.
    OSError
        For other low-level I/O failures when reading the archive.
    """
    if not path.exists():
        raise FileNotFoundError(f"docx not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"docx path is not a regular file: {path}")

    with zipfile.ZipFile(path) as zf:
        try:
            xml = zf.read("word/document.xml")
        except KeyError as exc:
            raise KeyError(f"archive {path} does not contain word/document.xml") from exc

    root = ET.fromstring(xml)
    body = root.find(f"{W_NS}body")
    if body is None:
        # Defensive: most often indicates a non-Word OOXML package or a
        # corrupted document.xml. Logging at WARNING is more discoverable
        # than silently returning "".
        logger.warning("no w:body element found in %s; returning empty text", path)
        return ""

    lines: list[str] = []
    for child in body:
        tag = child.tag
        if tag == f"{W_NS}p":
            text = _text_from_element(child).strip()
            if text:
                lines.append(text)
        elif tag == f"{W_NS}tbl":
            lines.append("")
            for tr in child.findall(f"{W_NS}tr"):
                row_cells: list[str] = []
                for tc in tr.findall(f"{W_NS}tc"):
                    cell_parts: list[str] = []
                    for p in tc.findall(f"{W_NS}p"):
                        pt = _text_from_element(p).strip()
                        if pt:
                            cell_parts.append(pt)
                    row_cells.append(" ".join(cell_parts))
                lines.append(" | ".join(row_cells))
            lines.append("")
        # Other body-level children (sectPr, sdt, etc.) are intentionally
        # ignored: they do not contribute user-visible body text.

    text = "\n".join(lines)
    # Collapse runs of 3+ blank lines down to a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: ``python _extract_docx_text.py <docx> [out.md]``."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: python _extract_docx_text.py <docx> [out.md]", file=sys.stderr)
        return 2

    src = Path(argv[0])
    out = Path(argv[1]) if len(argv) > 1 else src.with_suffix(".md")

    try:
        text = extract_docx(src)
    except (FileNotFoundError, IsADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        print(f"ERROR: failed to parse docx: {src} ({exc})", file=sys.stderr)
        return 3

    try:
        out.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: failed to write {out}: {exc}", file=sys.stderr)
        return 4

    print(f"Wrote {len(text)} chars -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
