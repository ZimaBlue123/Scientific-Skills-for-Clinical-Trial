"""Geometry sanity check for the generated deck.

Estimates the rendered height of every text box and every table cell and flags
elements whose content is likely to overflow their allotted height (which would
either spill visually or silently expand a table row).
"""

from __future__ import annotations

import math
from pathlib import Path

from pptx import Presentation

PPTX = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "汇报准备输出"
    / "TVAX-009_Ⅰ期细胞免疫与同类CpG佐剂乙肝疫苗对比分析.pptx"
)
OUT = Path(__file__).with_name("_overflow_check.txt")

EMU_IN = 914400.0
PT_IN = 72.0


def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x2E80 <= o <= 0x9FFF
        or 0x3000 <= o <= 0x30FF
        or 0xFF00 <= o <= 0xFFEF
        or 0x4E00 <= o <= 0x9FFF
    )


def text_width_in(text: str, size_pt: float, bold: bool) -> float:
    """Rough advance width in inches."""
    w_pt = 0.0
    for ch in text:
        if is_cjk(ch):
            w_pt += size_pt * (1.02 if bold else 1.00)
        elif ch == " ":
            w_pt += size_pt * 0.28
        else:
            w_pt += size_pt * (0.56 if bold else 0.52)
    return w_pt / PT_IN


def para_height_in(para, avail_w_in: float, default_size: float) -> float:
    runs = para.runs
    if not runs:
        text = ""
        size = default_size
        bold = False
    else:
        text = "".join(r.text for r in runs)
        size = runs[0].font.size.pt if runs[0].font.size else default_size
        bold = bool(runs[0].font.bold)
    ls = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
    sa = para.space_after.pt if para.space_after else 0.0
    if not text:
        return (size * ls + sa) / PT_IN
    width = text_width_in(text, size, bold)
    lines = max(1, math.ceil(width / max(avail_w_in, 0.05)))
    return (lines * size * ls + sa) / PT_IN


def frame_height_in(tf, avail_w_in: float, default_size: float = 12.0) -> float:
    total = 0.0
    for para in tf.paragraphs:
        total += para_height_in(para, avail_w_in, default_size)
    return total


def main() -> int:
    prs = Presentation(str(PPTX))
    lines: list[str] = [f"file: {PPTX.name}", f"slides: {len(prs.slides)}", ""]

    for idx, slide in enumerate(prs.slides, 1):
        problems: list[str] = []
        for sh in slide.shapes:
            # ---- plain text boxes -----------------------------------------
            if sh.has_text_frame and not sh.has_table:
                tf = sh.text_frame
                if not tf.text.strip():
                    continue
                w_in = (sh.width - tf.margin_left - tf.margin_right) / EMU_IN
                h_in = (sh.height - tf.margin_top - tf.margin_bottom) / EMU_IN
                need = frame_height_in(tf, w_in)
                # textboxes are allowed to grow downward slightly; flag only if
                # the overflow would push past the shape's own bottom by >0.06in
                if need > h_in + 0.06:
                    problems.append(
                        f"    [textbox] need {need:.2f}in vs box {h_in:.2f}in "
                        f"(w={w_in:.2f}) :: {tf.text[:46]!r}"
                    )
            # ---- tables ----------------------------------------------------
            if sh.has_table:
                tbl = sh.table
                for ri, row in enumerate(tbl.rows):
                    rh = row.height / EMU_IN
                    worst = 0.0
                    worst_txt = ""
                    for ci, cell in enumerate(row.cells):
                        cw = tbl.columns[ci].width / EMU_IN
                        avail = cw - (cell.margin_left + cell.margin_right) / EMU_IN
                        need = frame_height_in(cell.text_frame, avail, 10.0)
                        need += (cell.margin_top + cell.margin_bottom) / EMU_IN
                        if need > worst:
                            worst, worst_txt = need, cell.text[:40]
                    if worst > rh + 0.04:
                        problems.append(
                            f"    [table row {ri}] need {worst:.2f}in vs row {rh:.2f}in "
                            f":: {worst_txt!r}"
                        )
        if problems:
            lines.append(f"slide {idx}: {len(problems)} potential overflow(s)")
            lines.extend(problems)
    if not any(l.startswith("slide ") for l in lines):
        lines.append("OK - no overflow detected")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
