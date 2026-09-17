#!/usr/bin/env python3
"""Dump the Phase-1 CSR docx to plain text and pull out every paragraph /
table row that mentions cellular immunity, for the HEPLISAV-B comparison deck.

Usage:
    python extract_phase1_cellular_immunity.py
"""

from __future__ import annotations

from pathlib import Path

from docx import Document

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
SRC = (
    ROOT
    / "review_materials"
    / "临床"
    / "远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅰ期-临床研究总结报告-V1.0-20250618.docx"
)
OUT_FULL = ROOT / "scripts" / "_p1_csr_full.txt"
OUT_CELL = ROOT / "scripts" / "_p1_csr_cellular.txt"

KEYWORDS = [
    "细胞免疫",
    "ELISPOT",
    "Elispot",
    "胞内细胞因子",
    "ICS",
    "流式",
    "IFN",
    "IL-2",
    "IL-4",
    "TNF",
    "PBMC",
    "外周血单个核",
    "CD4",
    "CD8",
    "SFC",
    "斑点",
    "多功能",
    "细胞因子",
    "CTL",
    "Th1",
    "Th2",
    "刺激",
    "肽",
]


def iter_block_items(doc):
    """Yield paragraphs and tables in document order."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def main() -> int:
    doc = Document(str(SRC))
    lines: list[str] = []
    hits: list[str] = []

    n_table = 0
    for block in iter_block_items(doc):
        if hasattr(block, "rows"):  # table
            n_table += 1
            rows = []
            for row in block.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                # de-duplicate merged cells
                dedup: list[str] = []
                for c in cells:
                    if not dedup or dedup[-1] != c:
                        dedup.append(c)
                rows.append(" | ".join(dedup))
            text = "\n".join(rows)
            lines.append(f"\n<<<TABLE {n_table}>>>\n{text}\n<<<END TABLE>>>\n")
            if any(k in text for k in KEYWORDS):
                hits.append(f"\n<<<TABLE {n_table}>>>\n{text}\n<<<END TABLE>>>\n")
        else:
            t = block.text.strip()
            if not t:
                continue
            style = block.style.name if block.style is not None else ""
            prefix = f"[{style}] " if style and style != "Normal" else ""
            lines.append(prefix + t)
            if any(k in t for k in KEYWORDS):
                hits.append(prefix + t)

    OUT_FULL.write_text("\n".join(lines), encoding="utf-8")
    OUT_CELL.write_text("\n".join(hits), encoding="utf-8")
    print(f"full: {OUT_FULL}  ({len(lines)} blocks, {n_table} tables)")
    print(f"cellular hits: {OUT_CELL}  ({len(hits)} blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
