#!/usr/bin/env python3
"""Dump selected EDC domains (dm/ae/aes/dsic/dseos/dv/cm) of the TVAX-018-3 study export.

Writes review_materials/018-3/_work/refs/edc_keyforms.md for DSUR cross-checks.

Usage
-----
    py -3 scripts/dump_dsur0183_edc_keyforms.py
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "review_materials" / "018-3" / "前期资料"
XLSX = None
for p in SRC.iterdir():
    if p.name.startswith("YDSWXTVAX-018-3-001"):
        XLSX = p
        break
OUT = ROOT / "review_materials" / "018-3" / "_work" / "refs" / "edc_keyforms.md"

TARGETS = ["dm", "ae", "aes", "dsic", "dseos", "dssr", "dv", "cm", "subj", "ie"]


def main() -> int:
    if XLSX is None:
        print("study data xlsx not found")
        return 2
    wb = load_workbook(XLSX, data_only=True)
    lines = [f"# KEY FORMS: {XLSX.name}"]
    for name in TARGETS:
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        lines.append(f"\n## Sheet: {name} ({ws.max_row} rows x {ws.max_column} cols)")
        for r in range(1, min(ws.max_row or 0, 400) + 1):
            vals = []
            for c in range(1, (ws.max_column or 0) + 1):
                v = ws.cell(row=r, column=c).value
                if v is None:
                    continue
                s = str(v).replace("\n", " ").strip()
                if s:
                    vals.append(s)
            if vals:
                lines.append(" | ".join(vals))
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
