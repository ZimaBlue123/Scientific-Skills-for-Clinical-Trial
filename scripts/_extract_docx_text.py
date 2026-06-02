"""Extract plain text and tables from a .docx without external deps."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openformats.org/wordprocessingml/2006/main}"


def _text_from_element(el: ET.Element) -> str:
    parts: list[str] = []
    for node in el.iter():
        if node.tag == f"{W_NS}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W_NS}tab":
            parts.append("\t")
        elif node.tag in (f"{W_NS}br", f"{W_NS}cr"):
            parts.append("\n")
    return "".join(parts)


def extract_docx(path: Path) -> str:
    lines: list[str] = []
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(f"{W_NS}body")
    if body is None:
        return ""

    for child in body:
        if child.tag == f"{W_NS}p":
            t = _text_from_element(child).strip()
            if t:
                lines.append(t)
        elif child.tag == f"{W_NS}tbl":
            lines.append("")
            for ri, tr in enumerate(child.findall(f"{W_NS}tr")):
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

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python _extract_docx_text.py <docx> [out.md]", file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".md")
    text = extract_docx(src)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {len(text)} chars -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
