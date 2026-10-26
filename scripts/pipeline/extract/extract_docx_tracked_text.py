"""Extract text and tables from .docx using stdlib only (honoring tracked changes).

Handles tracked changes (``w:ins`` / ``w:del``): by default renders the ``final`` state
(keeps ``w:ins`` text, drops ``w:del`` text), or ``original`` state (drops ``w:ins``,
keeps ``w:del``). Preserves document body order for paragraphs and tables.

Usage:
    python scripts/pipeline/extract/extract_docx_tracked_text.py <file.docx> [-o out.txt] [--mode final|original]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def para_text(p: ET.Element, mode: str = "final") -> str:
    """Return text of a ``w:p`` element, honoring tracked changes."""
    parts: list[str] = []

    def walk(node: ET.Element, in_del: bool) -> None:
        for child in node:
            tag = child.tag
            if tag == f"{W}r":
                if child.find(f"{W}del") is not None:
                    continue
                if in_del and child.find(f"{W}delText") is not None:
                    continue
                for t in child.iter(f"{W}t"):
                    parts.append(t.text or "")
                for t in child.iter(f"{W}delText"):
                    if mode == "original":
                        parts.append(t.text or "")
            elif tag == f"{W}ins":
                if mode == "final":
                    walk(child, False)
            elif tag == f"{W}del":
                if mode == "original":
                    walk(child, True)
            elif tag in (
                f"{W}hyperlink",
                f"{W}sdt",
                f"{W}sdtContent",
                f"{W}smartTag",
                f"{W}smartTagPr",
                f"{W}dir",
                f"{W}bdo",
                f"{W}subDoc",
            ):
                walk(child, in_del)
            elif tag == f"{W}tab":
                parts.append("\t")
            elif tag == f"{W}br":
                parts.append(" ")

    walk(p, False)
    return "".join(parts).strip()


def iter_block_text(el: ET.Element, mode: str, out: list[str]) -> None:
    """Walk body-level paragraphs, tables, and structured document tags in order."""
    for child in el:
        if child.tag == f"{W}p":
            txt = para_text(child, mode)
            if txt:
                out.append(txt)
        elif child.tag == f"{W}tbl":
            for tr in child.findall(f"{W}tr"):
                cells: list[str] = []
                for tc in tr.findall(f"{W}tc"):
                    buf: list[str] = []
                    for p in tc.findall(f"{W}p"):
                        t = para_text(p, mode)
                        if t:
                            buf.append(t)
                    cells.append(" ".join(buf).strip())
                line = " | ".join(c for c in cells if c)
                if line:
                    out.append("[表] " + line)
            out.append("")
        elif child.tag == f"{W}sdt":
            content = child.find(f"{W}sdtContent")
            if content is not None:
                iter_block_text(content, mode, out)


def extract_tracked_docx(docx_path: Path | str, mode: str = "final") -> str:
    """Extract body-ordered text and tables from ``.docx`` in ``final`` or ``original`` revision state."""
    with zipfile.ZipFile(docx_path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(f"{W}body")
    out: list[str] = []
    if body is not None:
        iter_block_text(body, mode, out)
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract text and tables from .docx honoring tracked changes (stdlib only)."
    )
    parser.add_argument("docx_path", help="Source .docx file path")
    parser.add_argument("-o", "--output", default=None, help="Optional output text file path")
    parser.add_argument(
        "--mode",
        choices=("final", "original"),
        default="final",
        help="Revision state to render (default: final)",
    )
    args = parser.parse_args()

    src = Path(args.docx_path)
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 1

    text = extract_tracked_docx(src, mode=args.mode)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"written: {out} ({len(text)} chars)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["extract_tracked_docx", "para_text"]
