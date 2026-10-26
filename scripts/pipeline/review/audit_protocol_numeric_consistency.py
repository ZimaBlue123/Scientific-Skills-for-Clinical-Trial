#!/usr/bin/env python3
"""Cross-check numeric / placeholder consistency inside a converted protocol markdown.

Scans a `convert_to_md.py --mode numbered` output (##P## / ##T## markers) and reports:
  1) placeholder residues (XX / XXX / 待定 / <待定>)
  2) every occurrence of user-defined key numbers, with paragraph anchors
  3) unit-form inconsistencies (mL vs ml, mIU/mL vs mIU/ml)
  4) suspicious repeated-keyword sentences whose numbers differ

Usage
-----
    python scripts/audit_protocol_numeric_consistency.py <markdown> [--keys 3380,1920]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_KEYS = [
    "3380", "1920", "1460", "640", "730", "540", "621", "2010", "1370",
    "86.61", "0.1%", "15%", "5%", "95%", "90%", "2mIU", "10 mIU", "4.0~5.0",
]


def iter_blocks(text: str):
    """Yield (anchor, body) pairs split on '## P' / '## T' markers."""
    parts = re.split(r"^##\s+(P|T)(\d+)\s*$", text, flags=re.MULTILINE)
    # parts[0] is preamble; then (kind, num, body) triples
    for i in range(1, len(parts), 3):
        kind, num, body = parts[i], parts[i + 1], parts[i + 2]
        yield f"{kind}{num}", body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--keys", default=",".join(DEFAULT_KEYS))
    args = ap.parse_args()

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"ERROR: not found: {md_path}")
        return 2
    text = md_path.read_text(encoding="utf-8")
    blocks = list(iter_blocks(text))

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]

    print("=" * 78)
    print(f"FILE : {md_path.name}")
    print(f"BLOCKS: {len(blocks)}   CHARS: {len(text):,}")
    print("=" * 78)

    # 1) placeholders
    print("\n[1] PLACEHOLDER RESIDUES")
    ph_pat = re.compile(r"(XX+[~－\-]?XX*|XXX+|<待定>|待定|待补充|测试方法：XX|XX方法)")
    hits = 0
    for anchor, body in blocks:
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("|"):
                # tables: keep them, they matter too
                pass
            if ph_pat.search(line):
                snippet = line[:160]
                print(f"  {anchor:>6} | {snippet}")
                hits += 1
    if not hits:
        print("  (none)")

    # 2) key numbers
    print("\n[2] KEY NUMBER OCCURRENCES")
    for key in keys:
        rows = []
        pat = re.compile(re.escape(key) + r"(?![\d.])")
        for anchor, body in blocks:
            flat = " ".join(body.split())
            if pat.search(flat):
                for m in pat.finditer(flat):
                    s = max(0, m.start() - 45)
                    e = min(len(flat), m.end() + 45)
                    rows.append((anchor, flat[s:e]))
        if rows:
            print(f"\n  -- {key}  ({len(rows)} hit(s))")
            for anchor, snip in rows[:12]:
                print(f"     {anchor:>6} | ...{snip}...")
            if len(rows) > 12:
                print(f"     ... (+{len(rows) - 12} more)")

    # 3) unit form
    print("\n[3] UNIT FORM INCONSISTENCY (mL/ml)")
    lower = text.count("ml") - text.count("mL")
    if lower:
        for anchor, body in blocks:
            flat = " ".join(body.split())
            for m in re.finditer(r"\d+\s?(ml)(?![A-Za-z])", flat):
                s = max(0, m.start() - 30)
                print(f"  {anchor:>6} | ...{flat[s:m.end() + 20]}...")
    else:
        print("  (none)")

    # 4) duplicate concept with differing numbers
    print("\n[4] SAME-CONCEPT / DIFFERENT-VALUE WATCH")
    concepts = {
        "样本量合计": r"合计\s*(\d+)\s*例",
        "每组需要样本量": r"每组需要样本量为\s*(\d+)\s*例",
        "拟入组": r"拟(?:各组)?入组\s*(\d+)\s*例",
        "窗口期": r"窗口期[^\n]{0,40}?(\d+)\s*天",
    }
    for name, pat in concepts.items():
        seen: dict[str, list[str]] = {}
        for anchor, body in blocks:
            flat = " ".join(body.split())
            for m in re.finditer(pat, flat):
                seen.setdefault(m.group(1), []).append(anchor)
        if len(seen) > 1:
            print(f"  {name}:")
            for val, anchors in sorted(seen.items()):
                print(f"     value={val:>6}  anchors={anchors[:10]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
