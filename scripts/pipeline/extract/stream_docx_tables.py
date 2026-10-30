"""Stream-extract every table (and non-table paragraphs) from a very large .docx into TSV files.

Designed for multi-hundred-MB listing documents (e.g. CSR data listings) where
``python-docx`` would exhaust memory: ``word/document.xml`` is parsed with
``lxml.etree.iterparse`` and processed elements are released immediately.

Outputs (in ``out_dir``)::

    table_01.tsv, table_02.tsv, ...   one row per <w:tr>, cells tab-separated
    paragraphs.txt                    body paragraphs that are not inside a table

CLI::

    python scripts/pipeline/extract/stream_docx_tables.py <input.docx> <out_dir> [--no-paragraphs]
"""

from __future__ import annotations

import argparse
import logging
import sys
import zipfile
from pathlib import Path

from lxml import etree

__all__ = ["stream_extract_docx_tables"]

logger = logging.getLogger(__name__)

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _node_text(el: etree._Element) -> str:
    parts: list[str] = []
    for node in el.iter(f"{W_NS}t", f"{W_NS}tab", f"{W_NS}br"):
        if node.tag == f"{W_NS}t":
            parts.append(node.text or "")
        else:
            parts.append(" ")
    # TSV safety: no embedded tabs/newlines inside a cell
    return " ".join("".join(parts).split())


def _release(el: etree._Element) -> None:
    el.clear()
    parent = el.getparent()
    if parent is not None:
        while el.getprevious() is not None:
            del parent[0]


def stream_extract_docx_tables(src: str | Path, out_dir: str | Path, paragraphs: bool = True) -> dict[str, int]:
    """Extract tables (and optionally paragraphs) from ``src`` into ``out_dir``.

    Returns ``{"tables": <count>, "rows": <total rows>, "paragraphs": <count>}``.
    Nested tables are flattened into their outermost table.
    """
    src = Path(src)
    out = Path(out_dir)
    if not src.is_file():
        raise FileNotFoundError(f"input not found: {src}")
    try:
        with zipfile.ZipFile(src) as zf:
            if "word/document.xml" not in zf.namelist():
                raise ValueError(f"not a WordprocessingML package (missing word/document.xml): {src}")
            out.mkdir(parents=True, exist_ok=True)
            stats = {"tables": 0, "rows": 0, "paragraphs": 0}

            with zf.open("word/document.xml") as fh:
                for _, tbl in etree.iterparse(fh, events=("end",), tag=f"{W_NS}tbl", huge_tree=True, recover=True):
                    if any(a.tag == f"{W_NS}tbl" for a in tbl.iterancestors()):
                        continue  # nested table: handled by its outer table
                    stats["tables"] += 1
                    path = out / f"table_{stats['tables']:02d}.tsv"
                    rows = 0
                    with path.open("w", encoding="utf-8", newline="\n") as tsv:
                        for tr in tbl.iter(f"{W_NS}tr"):
                            tsv.write("\t".join(_node_text(tc) for tc in tr.iter(f"{W_NS}tc")) + "\n")
                            rows += 1
                    stats["rows"] += rows
                    logger.info("%s rows=%d", path.name, rows)
                    _release(tbl)

            if paragraphs:
                with zf.open("word/document.xml") as fh, (out / "paragraphs.txt").open("w", encoding="utf-8", newline="\n") as pf:
                    for _, p in etree.iterparse(fh, events=("end",), tag=f"{W_NS}p", huge_tree=True, recover=True):
                        if not any(a.tag == f"{W_NS}tbl" for a in p.iterancestors()):
                            txt = _node_text(p)
                            if txt:
                                pf.write(txt + "\n")
                                stats["paragraphs"] += 1
                        # only release top-level paragraphs; table content is already skipped
                        if p.getparent() is not None and p.getparent().tag == f"{W_NS}body":
                            _release(p)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"not a valid .docx (zip) file: {src}") from exc
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stream-extract tables from a large .docx into TSV files.")
    parser.add_argument("src", type=Path, help="input .docx")
    parser.add_argument("out_dir", type=Path, help="output directory")
    parser.add_argument("--no-paragraphs", action="store_true", help="skip paragraphs.txt")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        stats = stream_extract_docx_tables(args.src, args.out_dir, paragraphs=not args.no_paragraphs)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"done: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
