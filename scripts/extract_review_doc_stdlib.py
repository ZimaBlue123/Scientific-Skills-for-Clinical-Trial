#!/usr/bin/env python3
"""
Robust extractor for review_materials/*.docx using only Python stdlib.

Why stdlib-only?
----------------
This project may run on machines that lack ``python-docx`` (e.g. minimal CI
images, msys64 environments). We can still parse modern .docx files because
they are ZIP containers with a well-defined XML payload at
``word/document.xml``.

Usage
-----
    py -3 scripts/extract_review_doc_stdlib.py \\
        [INPUT_DIR | INPUT_FILE] [-o OUTPUT_FILE]

By default:
    * INPUT_DIR  -> E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials
    * OUTPUT     -> <workspace>/extracted_review_doc.txt

Exit codes
----------
    0  success
    1  no .docx file discovered
    2  I/O or parsing error
"""
from __future__ import annotations

import argparse
import logging
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path
from xml.etree import ElementTree as ET

# Word XML namespace. Bound at module level for readability + speed.
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

DEFAULT_INPUT = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials"
)
DEFAULT_OUTPUT = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\extracted_review_doc.txt"
)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("extract_review_doc_stdlib")


def _local(tag: str) -> str:
    """Strip namespace from an ElementTree tag (e.g. ``{ns}p`` -> ``p``)."""
    return tag.rsplit("}", 1)[-1]


def extract_docx(docx_path: Path) -> str:
    """Extract paragraph + table text from a .docx in document order.

    The extraction walks ``word/document.xml`` in the order of <w:body>
    children, preserving paragraph breaks and emitting one row per table
    line (joined by `` | `` to keep flat-text output diff-friendly).

    Parameters
    ----------
    docx_path : Path
        The .docx file.

    Returns
    -------
    str
        Concatenated text separated by ``\\n``. Empty string if the
        document body contains no text.
    """
    if not docx_path.exists():
        raise FileNotFoundError(f"docx not found: {docx_path}")
    if not docx_path.is_file():
        raise IsADirectoryError(f"not a regular file: {docx_path}")

    try:
        with zipfile.ZipFile(docx_path) as z:
            names = z.namelist()
            if "word/document.xml" not in names:
                raise KeyError("word/document.xml missing from docx archive")
            with z.open("word/document.xml") as fh:
                xml_bytes = fh.read()
    except zipfile.BadZipFile as exc:
        raise ValueError(f"corrupted docx (bad zip): {docx_path}") from exc

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"corrupted docx (xml parse error): {docx_path}") from exc

    body = root.find("w:body", NS)
    if body is None:
        logger.warning("no <w:body> element in %s", docx_path.name)
        return ""

    lines: list[str] = []
    for child in body:
        kind = _local(child.tag)
        if kind == "p":
            text = "".join(t.text or "" for t in child.iter(f"{{{W_NS}}}t"))
            lines.append(text)
        elif kind == "tbl":
            for row in child.findall("w:tr", NS):
                cells = [
                    "".join(t.text or "" for t in cell.iter(f"{{{W_NS}}}t")).strip()
                    for cell in row.findall("w:tc", NS)
                ]
                cells = [c for c in cells if c]
                if cells:
                    lines.append(" | ".join(cells))
        # ``sectPr`` and other non-textual block elements are skipped.
    return "\n".join(lines)


def iter_docx_targets(input_path: Path) -> Iterator[Path]:
    """Yield .docx files from either a file or a directory."""
    if not input_path.exists():
        raise FileNotFoundError(f"input does not exist: {input_path}")
    if input_path.is_dir():
        for p in sorted(input_path.iterdir()):
            if p.suffix.lower() == ".docx":
                yield p
    elif input_path.is_file() and input_path.suffix.lower() == ".docx":
        yield input_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from .docx using Python stdlib (no python-docx)."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input .docx file or directory (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output text file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=LOG_FORMAT,
    )

    try:
        targets = list(iter_docx_targets(args.input))
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2

    if not targets:
        logger.error("no .docx files found under %s", args.input)
        return 1

    logger.info("found %d .docx file(s) under %s", len(targets), args.input)

    merged: list[str] = []
    for f in targets:
        logger.info("extracting: %s", f.name)
        try:
            text = extract_docx(f)
        except (FileNotFoundError, IsADirectoryError, ValueError) as exc:
            logger.error("failed to extract %s: %s", f.name, exc)
            return 2
        if not text:
            logger.warning("%s contained no extractable text", f.name)
            continue
        merged.append(f"=== {f.name} ===\n{text}")

    final = "\n\n".join(merged) + "\n"
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(final, encoding="utf-8")
    except OSError as exc:
        logger.error("failed to write %s: %s", args.output, exc)
        return 2

    logger.info(
        "wrote %d chars to %s (sources=%d)",
        len(final),
        args.output,
        len(merged),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
