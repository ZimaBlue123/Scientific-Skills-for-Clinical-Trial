"""RTF (Rich Text Format) ingestion module for clinical TFLs and listings.

Handles SAS/RTF clinical trial tables where rows are delimited by ``\\trowd`` / ``\\row``,
cells by ``\\cell``, and CJK characters by ``\\'hh`` (CP936/GB18030 hex escapes) or
``\\uN`` Unicode escapes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_HEX = re.compile(rb"\\'([0-9a-fA-F]{2})")
_CTRL = re.compile(rb"\\[a-zA-Z]+-?\d* ?")
_SPLIT_CELL = re.compile(rb"\\cell(?![a-zA-Z])")
_UNI = re.compile(rb"\\u(-?\d+)\??")
_ROW_END = re.compile(rb"\\row(?![a-zA-Z])")
_TABLE_TITLE = re.compile(r"(表格|表|清单|附图|Table|Listing|Figure)\s*\d+", re.IGNORECASE)


def decode_rtf_bytes(block: bytes, encoding: str = "gb18030") -> str:
    """Decode an RTF byte fragment into clean readable text."""

    def _u(match: re.Match[bytes]) -> bytes:
        code = int(match.group(1))
        cp = code & 0xFFFF if code >= 0 else 65536 + code
        return chr(cp).encode(encoding, errors="ignore")

    b = re.sub(rb"\{\\\*[^}]*\}", b"", block)
    b = _UNI.sub(_u, b)
    b = _HEX.sub(lambda m: bytes([int(m.group(1), 16)]), b)
    b = _CTRL.sub(b" ", b)
    b = re.sub(rb"[{}]", b" ", b)
    b = re.sub(rb"[\r\n\t]+", b" ", b)
    text = b.decode(encoding, errors="ignore")
    return re.sub(r" +", " ", text).strip()


def extract_rtf_text(rtf_path: Path | str, encoding: str = "gb18030") -> str:
    """Extract plain text and tab-delimited table rows from an RTF file."""
    raw = Path(rtf_path).read_bytes()
    b = re.sub(rb"\{\\\*[^}]*\}", b"", raw)
    b = _HEX.sub(lambda m: bytes([int(m.group(1), 16)]), b)
    b = re.sub(rb"\\cell(?![a-zA-Z])", b"\t", b)
    b = re.sub(rb"\\(row|par|line)(?![a-zA-Z])", b"\n", b)
    b = re.sub(rb"\\[a-zA-Z]+(-?[0-9]+)?(\s|(?=[^a-zA-Z0-9]))", b"", b)
    b = b.replace(b"{", b"").replace(b"}", b"")
    text = b.decode(encoding, errors="ignore")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def extract_rtf_tables(
    rtf_path: Path | str,
    keyword: str | None = None,
    encoding: str = "gb18030",
) -> list[dict[str, Any]]:
    """Parse RTF tables into structured ``[{"title": str, "rows": list[list[str]]}]``."""
    raw = Path(rtf_path).read_bytes()
    ends = [m.start() for m in _ROW_END.finditer(raw)]
    marks: list[tuple[int, int]] = []
    prev = 0
    for end_pos in ends:
        marks.append((prev, end_pos))
        prev = end_pos + 4

    tables: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for start_pos, end_pos in marks:
        block = raw[start_pos:end_pos]
        first_cell = _SPLIT_CELL.search(block)
        if first_cell is None:
            continue
        pre = decode_rtf_bytes(block[: first_cell.start()], encoding=encoding)
        parts = _SPLIT_CELL.split(block)
        cells = [decode_rtf_bytes(p, encoding=encoding) for p in parts[:-1]]
        if not any(cells):
            continue
        if _TABLE_TITLE.search(pre):
            if cur and cur["rows"]:
                tables.append(cur)
            cur = {"title": pre, "rows": []}
        if cur is None:
            cur = {"title": pre or "", "rows": []}
        cur["rows"].append(cells)

    if cur and cur["rows"]:
        tables.append(cur)

    if keyword:
        kw_norm = re.sub(r"\s+", "", keyword)
        tables = [
            tb for tb in tables if kw_norm in re.sub(r"\s+", "", tb.get("title", ""))
        ]
    return tables


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract plain text or structured TFL tables from SAS/Word RTF files."
    )
    parser.add_argument("rtf_path", help="Path to source .rtf file")
    parser.add_argument(
        "--tables",
        action="store_true",
        help="Parse structured tables instead of flat text",
    )
    parser.add_argument(
        "--grep",
        default=None,
        help="Filter tables whose title matches keyword (ignores whitespace)",
    )
    parser.add_argument("-o", "--output", default=None, help="Output file path (.txt or .json)")
    args = parser.parse_args()

    src = Path(args.rtf_path)
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 1

    if args.tables or args.grep:
        tables = extract_rtf_tables(src, keyword=args.grep)
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Saved {len(tables)} tables -> {out}")
        else:
            for idx, tb in enumerate(tables):
                print(f"\n##### TBL#{idx} | {tb['title'][:120]}")
                for r in tb["rows"]:
                    print("   " + " | ".join(r))
    else:
        text = extract_rtf_text(src)
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            print(f"Saved {len(text)} chars -> {out}")
        else:
            print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["decode_rtf_bytes", "extract_rtf_text", "extract_rtf_tables"]
