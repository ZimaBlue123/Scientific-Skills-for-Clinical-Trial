"""Geometry sanity check for the generated deck.

Estimates or strictly measures the rendered height of every text box and every table cell and flags
elements whose content is likely to overflow their allotted height (which would
either spill visually or silently expand a table row).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from pptx import Presentation

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


def run_com_check(pptx_path: Path, out_path: Path) -> int:
    import win32com.client  # type: ignore

    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(pptx_path), ReadOnly=True, WithWindow=False)
    buf: list[str] = [f"file: {pptx_path.name}", f"slides: {pres.Slides.Count}", ""]
    n_prob = 0
    try:
        for i in range(1, pres.Slides.Count + 1):
            slide = pres.Slides(i)
            problems: list[str] = []
            for sh in slide.Shapes:
                try:
                    has_tf = bool(sh.HasTextFrame)
                except Exception:  # noqa: BLE001
                    continue
                if not has_tf:
                    continue
                tf2 = sh.TextFrame2
                try:
                    txt = tf2.TextRange.Text or ""
                except Exception:  # noqa: BLE001
                    continue
                if not txt.strip():
                    continue
                try:
                    bound_h = float(tf2.TextRange.BoundHeight)
                    bound_w = float(tf2.TextRange.BoundWidth)
                except Exception:  # noqa: BLE001
                    continue
                avail_h = float(sh.Height) - (float(tf2.MarginTop) + float(tf2.MarginBottom))
                avail_w = float(sh.Width) - (float(tf2.MarginLeft) + float(tf2.MarginRight))
                autofit = int(sh.TextFrame2.AutoSize)
                # 0 = none (text may overflow), 1 = shrink on overflow,
                # 2 = shape grows with text
                # tolerance of 1 pt expressed in EMU (1 pt = 12700 EMU)
                TOL = 12700.0 * 2
                if bound_h > avail_h + TOL and autofit != 1:
                    problems.append(
                        f"    text {bound_h / EMU_IN:.2f}in > box {avail_h / EMU_IN:.2f}in "
                        f"(+{(bound_h - avail_h) / EMU_IN:.2f}) autosize={autofit} "
                        f":: {txt[:50]!r}"
                    )
                if bound_w > avail_w + TOL:
                    problems.append(
                        f"    WIDTH {bound_w / EMU_IN:.2f}in > {avail_w / EMU_IN:.2f}in "
                        f":: {txt[:50]!r}"
                    )
            if problems:
                n_prob += len(problems)
                buf.append(f"slide {i}: {len(problems)} issue(s)")
                buf.extend(problems)
        if n_prob == 0:
            buf.append("OK - no overflow detected (PowerPoint COM)")
    finally:
        pres.Close()

    out_path.write_text("\n".join(buf), encoding="utf-8")
    return 0


def run_heuristic_check(pptx_path: Path, out_path: Path) -> int:
    prs = Presentation(str(pptx_path))
    lines: list[str] = [f"file: {pptx_path.name}", f"slides: {len(prs.slides)}", ""]

    for idx, slide in enumerate(prs.slides, 1):
        problems: list[str] = []
        for sh in slide.shapes:
            if sh.has_text_frame and not sh.has_table:
                tf = sh.text_frame
                if not tf.text.strip():
                    continue
                w_in = (sh.width - tf.margin_left - tf.margin_right) / EMU_IN
                h_in = (sh.height - tf.margin_top - tf.margin_bottom) / EMU_IN
                need = frame_height_in(tf, w_in)
                if need > h_in + 0.06:
                    problems.append(
                        f"    [textbox] need {need:.2f}in vs box {h_in:.2f}in "
                        f"(w={w_in:.2f}) :: {tf.text[:46]!r}"
                    )
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
        lines.append("OK - no overflow detected (Heuristic)")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check PPTX for text overflow.")
    parser.add_argument("pptx_file", type=Path, help="Path to the PPTX file to check.")
    parser.add_argument(
        "--out", "-o", type=Path, default=None, help="Output TXT file (defaults to *_overflow.txt)."
    )
    parser.add_argument(
        "--force-heuristic",
        action="store_true",
        help="Force python-pptx heuristic mode instead of COM.",
    )
    args = parser.parse_args(argv)

    pptx_path: Path = args.pptx_file
    if not pptx_path.is_file():
        print(f"Error: file not found: {pptx_path}")
        return 1

    out_path: Path = args.out or pptx_path.with_name(f"{pptx_path.stem}_overflow.txt")

    if not args.force_heuristic and sys.platform == "win32":
        try:
            print("Attempting authoritative PowerPoint COM check...")
            return run_com_check(pptx_path, out_path)
        except Exception as e:
            print(f"COM check failed ({e}). Falling back to heuristic check...")
            return run_heuristic_check(pptx_path, out_path)
    else:
        print("Running python-pptx heuristic check...")
        return run_heuristic_check(pptx_path, out_path)


if __name__ == "__main__":
    sys.exit(main())
