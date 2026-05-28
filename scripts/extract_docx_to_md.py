from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable, List, Optional, Tuple

_DOCX_IMPORT_ERROR: Exception | None = None
try:
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ModuleNotFoundError as e:  # pragma: no cover
    # Optional dependency: keep the script importable for tooling (compileall)
    _DOCX_IMPORT_ERROR = e


def iter_block_items(doc: Document) -> Iterable[Tuple[str, object]]:
    """
    Yield ('p', Paragraph) and ('tbl', Table) in document order.
    """
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield ("p", Paragraph(child, doc))
        elif isinstance(child, CT_Tbl):
            yield ("tbl", Table(child, doc))


def _clean_cell_text(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def table_to_md(table: Table, max_cols: Optional[int] = None) -> str:
    rows: List[List[str]] = []
    for row in table.rows:
        cells = [_clean_cell_text(cell.text) for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ""

    ncol = max(len(r) for r in rows)
    if max_cols is not None:
        ncol = min(ncol, max_cols)

    norm: List[List[str]] = []
    for r in rows:
        r2 = (r + [""] * (ncol - len(r)))[:ncol]
        norm.append(r2)

    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []

    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * ncol) + " |",
    ]
    for r in body:
        md_lines.append("| " + " | ".join(r) + " |")
    return "\n".join(md_lines)


def docx_to_md(src_path: Path, max_cols: Optional[int] = None) -> str:
    if _DOCX_IMPORT_ERROR is not None:  # pragma: no cover
        raise _DOCX_IMPORT_ERROR
    doc = Document(str(src_path))

    out: List[str] = []
    out.append(f"# Source: {src_path.name}")
    out.append("")

    para_idx = 0
    table_idx = 0

    for kind, item in iter_block_items(doc):
        if kind == "p":
            p: Paragraph = item  # type: ignore[assignment]
            text = " ".join(p.text.split())
            if not text:
                continue
            para_idx += 1
            out.append(f"## P{para_idx}")
            out.append(text)
            out.append("")
        else:
            t: Table = item  # type: ignore[assignment]
            md = table_to_md(t, max_cols=max_cols)
            if not md.strip():
                continue
            table_idx += 1
            out.append(f"## T{table_idx}")
            out.append(md)
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract DOCX paragraphs/tables to markdown.")
    parser.add_argument("--input", required=True, help="Input .docx path")
    parser.add_argument("--output", required=True, help="Output .md path")
    parser.add_argument("--max-cols", type=int, default=None, help="Max columns when rendering tables")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    if not src.exists() or not src.is_file():
        print(f"ERROR: input file not found: {src}", file=sys.stderr)
        return 2
    if src.suffix.lower() != ".docx":
        print(f"ERROR: input must be a .docx file: {src}", file=sys.stderr)
        return 2
    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        md = docx_to_md(src, max_cols=args.max_cols)
    except ModuleNotFoundError:
        print(
            "ERROR: missing dependency 'python-docx'. Install via:\n"
            "  python -m pip install python-docx",
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        print(f"ERROR: failed to parse docx: {src}\n{e}", file=sys.stderr)
        return 1

    # Ensure trailing newline for POSIX-friendly diffs
    if not md.endswith("\n"):
        md += "\n"

    try:
        dst.write_text(md, encoding="utf-8")
    except Exception as e:
        print(f"ERROR: failed to write markdown: {dst}\n{e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

