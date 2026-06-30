#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract text/content from .xlsx files (UTF-8, robust).

Why this exists
---------------
``openpyxl.load_workbook`` raises ``ValueError`` when an .xlsx contains
non-conforming XML such as ``<autoFilter ref="...">`` with cell references
outside the canonical pattern. Several real-world EDC exports (e.g. some
Taimei/Taibo/Tongxin exports used by Chinese vaccine clinical trials) ship
with this kind of legacy artifact.

This script parses the .xlsx zip + workbook.xml + sharedStrings.xml directly,
which is robust to that failure mode and still preserves all cell text and
numeric content.

Usage
-----
    # Single file -> stdout
    py -3 scripts/extract_xlsx_full.py workbook.xlsx

    # Single file -> output file
    py -3 scripts/extract_xlsx_full.py workbook.xlsx -o dump.txt

    # Batch a folder
    py -3 scripts/extract_xlsx_full.py some_folder/ -o combined_dump.txt

Output format
-------------
One section per sheet, separated by 78 '#' chars. Each non-empty row is
written as ``R{nnnn}: cell1 | cell2 | ...`` with newlines inside cells
collapsed to `` ⏎ ``.

Dependencies
------------
stdlib only (zipfile + xml.etree.ElementTree).
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

LOG_FORMAT = "%(asctime)s [%(levelname)s] extract_xlsx_full: %(message)s"
logger = logging.getLogger("extract_xlsx_full")
ENCODING = "utf-8"

NS = {
    "n": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

# Pre-compiled regexes for cell reference parsing.
_REF_RE = re.compile(r"([A-Za-z]+)(\d+)(?::([A-Za-z]+)(\d+))?$")
_COL_LETTERS_RE = re.compile(r"([A-Za-z]+)")


def _col_letters_to_idx(s: str) -> int:
    """A -> 0, B -> 1, ..., AA -> 26, etc.

    Non-letter characters are ignored to stay robust against malformed
    cell references (e.g. ``A1$`` from legacy EDC exports).
    """
    n = 0
    for ch in s:
        u = ch.upper()
        if not ("A" <= u <= "Z"):
            continue
        n = n * 26 + (ord(u) - 64)
    return n - 1


def _split_ref(ref: str) -> Tuple[int, int]:
    """Split ``A1`` or ``A1:B3`` into ((c1, r1), (c2, r2))."""
    m = _REF_RE.match(ref)
    if not m:
        return ((-1, -1), (-1, -1))
    c1 = _col_letters_to_idx(m.group(1))
    r1 = int(m.group(2)) - 1
    if m.group(3):
        c2 = _col_letters_to_idx(m.group(3))
        r2 = int(m.group(4)) - 1
    else:
        c2, r2 = c1, r1
    return ((c1, r1), (c2, r2))


def _load_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    """Return the workbook's shared string table (decoded as text)."""
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        logger.warning("sharedStrings.xml parse error: %s", e)
        return []
    out: List[str] = []
    for si in root.findall("n:si", NS):
        # concatenate all <t> nodes (handles rich text via <r>)
        text = "".join((t.text or "") for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
        out.append(text)
    return out


def _load_sheet_targets(zf: zipfile.ZipFile) -> List[Tuple[str, str]]:
    """Return [(sheet_name, sheet_target_path), ...] in workbook order."""
    try:
        wb_xml = ET.fromstring(zf.read("xl/workbook.xml"))
    except ET.ParseError as e:
        logger.warning("workbook.xml parse error: %s", e)
        return []
    sheets_meta: List[Tuple[str, str]] = []
    sheets = wb_xml.find("n:sheets", NS)
    if sheets is None:
        return []
    for s in sheets.findall("n:sheet", NS):
        name = s.attrib.get("name", "")
        rid = s.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        sheets_meta.append((name, rid))

    rels: dict[str, str] = {}
    try:
        rx = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except (KeyError, ET.ParseError) as e:
        if isinstance(e, ET.ParseError):
            logger.warning("workbook.xml.rels parse error: %s", e)
        rx = None
    if rx is not None:
        for r in rx:
            rels[r.attrib.get("Id", "")] = r.attrib.get("Target", "")
    return [(name, _resolve_target(rels.get(rid, ""))) for name, rid in sheets_meta]


def _resolve_target(target: str) -> str:
    if not target:
        return ""
    if target.startswith("xl/"):
        return target
    return "xl/" + target


def _iter_sheet_rows(
    zf: zipfile.ZipFile,
    path: str,
    sst: List[str],
) -> Iterator[Tuple[int, List[str]]]:
    """Yield (row_idx_1based, [cell_text_in_column_order]) for a sheet."""
    try:
        raw = zf.read(path)
    except KeyError:
        return
    try:
        ws = ET.fromstring(raw)
    except ET.ParseError as e:
        logger.warning("ParseError in %s: %s", path, e)
        return

    # Collect merged cell ranges so empty trailing cells inherit values.
    merged: List[Tuple[int, int, int, int]] = []
    for mc in ws.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}mergeCell"):
        ref = mc.attrib.get("ref", "")
        if ":" not in ref:
            continue
        (c1, r1), (c2, r2) = _split_ref(ref.split(":", 1)[0]), _split_ref(ref.split(":", 1)[1])
        if c1 < 0 or r1 < 0 or c2 < 0 or r2 < 0:
            continue
        merged.append((c1, r1, c2, r2))

    sheet_data = ws.find("n:sheetData", NS)
    if sheet_data is None:
        return

    for row in sheet_data.findall("n:row", NS):
        try:
            r_attr = int(row.attrib.get("r", "0"))
        except ValueError:
            continue
        row_cells: dict[int, str] = {}
        for c in row.findall("n:c", NS):
            ref = c.attrib.get("r", "")
            t = c.attrib.get("t", "n")
            v_el = c.find("n:v", NS)
            is_el = c.find("n:is", NS)
            val = ""
            if t == "s" and v_el is not None and v_el.text is not None:
                try:
                    val = sst[int(v_el.text)]
                except (ValueError, IndexError):
                    val = f"<sst!{v_el.text}>"
            elif t == "inlineStr" and is_el is not None:
                val = "".join(
                    (tt.text or "")
                    for tt in is_el.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                )
            elif t == "b" and v_el is not None:
                val = "TRUE" if v_el.text == "1" else "FALSE"
            elif v_el is not None:
                val = v_el.text or ""
            # extract column index
            col_m = _COL_LETTERS_RE.match(ref)
            if col_m:
                row_cells[_col_letters_to_idx(col_m.group(1))] = val

        # Apply merged ranges for this row.
        for (c1, r1, c2, r2) in merged:
            if r1 <= r_attr - 1 <= r2 and c1 in row_cells:
                for cc in range(c1, c2 + 1):
                    row_cells.setdefault(cc, row_cells[c1])

        if any(v.strip() for v in row_cells.values()):
            # Sort by column index for stable column order across sheets.
            ordered = [row_cells.get(i, "") for i in sorted(row_cells)]
            yield r_attr, ordered


def extract_xlsx(xlsx_path: Path) -> str:
    """Dump every sheet of *xlsx_path* as UTF-8 text."""
    out: List[str] = [f"# FILE: {xlsx_path.name}", f"# Path: {xlsx_path}"]
    try:
        with zipfile.ZipFile(str(xlsx_path)) as zf:
            names = zf.namelist()
            sst = _load_shared_strings(zf)
            sheets = _load_sheet_targets(zf)
            out.append(f"# Sheets ({len(sheets)}): {[s[0] for s in sheets]}")
            for sheet_name, target in sheets:
                out.append("")
                out.append("#" * 78)
                out.append(f"# Sheet: {sheet_name}  path={target}")
                out.append("#" * 78)
                if not target or target not in names:
                    out.append(f"# (missing sheet path: {target})")
                    continue
                for r_idx, cells in _iter_sheet_rows(zf, target, sst):
                    cells_out = [c.replace("\n", " ⏎ ") for c in cells]
                    out.append(f"R{r_idx:04d}: " + " | ".join(cells_out))
    except zipfile.BadZipFile as e:
        logger.error("not a valid .xlsx (bad zip): %s: %s", xlsx_path, e)
        return f"# FILE: {xlsx_path.name}\n# ERROR: bad zip: {e}"
    except OSError as e:
        logger.error("I/O error reading %s: %s", xlsx_path, e)
        return f"# FILE: {xlsx_path.name}\n# ERROR: I/O: {e}"
    return "\n".join(out)


def _iter_xlsx_files(target: Path) -> Iterator[Path]:
    if target.is_file():
        yield target
        return
    if not target.is_dir():
        return
    for entry in sorted(target.iterdir()):
        if entry.suffix.lower() == ".xlsx" and not entry.name.startswith("~"):
            yield entry


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Robust .xlsx -> UTF-8 text dumper (zip+xml).")
    parser.add_argument("target", help=".xlsx file or folder containing .xlsx files")
    parser.add_argument("-o", "--output", default=None, help="output file (default: stdout)")
    parser.add_argument("--log-level", default="WARNING")
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.WARNING), format=LOG_FORMAT)

    target = Path(args.target)
    if not target.exists():
        logger.error("Path not found: %s", target)
        return 2

    chunks: List[str] = []
    for xlsx in _iter_xlsx_files(target):
        logger.info("processing %s", xlsx)
        chunks.append(extract_xlsx(xlsx))

    text = "\n".join(chunks)
    if args.output:
        out_path = Path(args.output)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding=ENCODING)
        except OSError as e:
            logger.error("failed to write %s: %s", out_path, e)
            return 1
        print(f"OK: wrote {args.output} ({len(text):,} chars)")
    else:
        try:
            sys.stdout.reconfigure(encoding=ENCODING, errors="replace")
        except Exception:  # noqa: BLE001 - some streams are not reconfigurable
            pass
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
