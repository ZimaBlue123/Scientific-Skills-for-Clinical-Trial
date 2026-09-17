#!/usr/bin/env python3
"""Inspect PPTX slide layout details (shape geometry, fonts, colors) for a
given set of 1-based slide indices.

Usage:
    python inspect_pptx_layout.py <pptx> <out.txt> [slide_numbers...]
"""

from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu


def emu_to_in(v) -> str:
    try:
        return f"{Emu(int(v)).inches:.3f}in"
    except Exception:  # noqa: BLE001
        return str(v)


def fmt_color(font) -> str:
    try:
        if font.color and font.color.type is not None:
            if font.color.type == 1:  # MSO_THEME_COLOR
                return f"theme:{font.color.theme_color}"
            rgb = font.color.rgb
            return f"#{rgb}"
    except Exception:  # noqa: BLE001
        pass
    return "-"


def dump_run(run, prefix=""):
    f = run.font
    sz = f.size.pt if f.size is not None else None
    lines = [
        f"{prefix}run: {run.text!r}",
        f"{prefix}  font={f.name!r} size={sz} bold={f.bold} italic={f.italic} color={fmt_color(f)}",
    ]
    return lines


def dump_tf(tf, indent="    "):
    out = []
    for pi, para in enumerate(tf.paragraphs):
        runs = list(para.runs)
        if not runs and not para.text.strip():
            continue
        out.append(f"{indent}[p{pi}] align={para.alignment} level={para.level}")
        for r in runs:
            out.extend(dump_run(r, indent + "  "))
    return out


def dump_cell(cell, indent="    "):
    out = [f"{indent}cell:"]
    for pi, para in enumerate(cell.text_frame.paragraphs):
        runs = list(para.runs)
        if not runs and not para.text.strip():
            continue
        out.append(f"{indent}  [p{pi}] align={para.alignment}")
        for r in runs:
            out.extend(dump_run(r, indent + "    "))
    return out


def main(argv: list[str]) -> int:
    src = Path(argv[1])
    out_path = Path(argv[2])
    wanted = [int(x) for x in argv[3:]] if len(argv) > 3 else []

    prs = Presentation(str(src))
    lines: list[str] = []
    lines.append(
        f"Slide size: {emu_to_in(prs.slide_width)} x {emu_to_in(prs.slide_height)}"
        f"  ({prs.slide_width} x {prs.slide_height} EMU)"
    )
    lines.append(f"Total slides: {len(prs.slides)}")
    lines.append("")

    for idx, slide in enumerate(prs.slides, 1):
        if wanted and idx not in wanted:
            continue
        lines.append(f"########## SLIDE {idx}  layout={slide.slide_layout.name!r} ##########")
        for sh in slide.shapes:
            lines.append(
                f"  - name={sh.name!r} type={sh.shape_type} "
                f"L={emu_to_in(sh.left)} T={emu_to_in(sh.top)} "
                f"W={emu_to_in(sh.width)} H={emu_to_in(sh.height)}"
            )
            if sh.has_text_frame:
                lines.extend(dump_tf(sh.text_frame))
            if getattr(sh, "has_table", False) and sh.has_table:
                tbl = sh.table
                lines.append(f"    TABLE rows={len(tbl.rows)} cols={len(tbl.columns)}")
                try:
                    from pptx.util import Emu as _E

                    widths = [f"{_E(c.width).inches:.2f}" for c in tbl.columns]
                    lines.append(f"    col widths(in)={widths}")
                    heights = [f"{_E(r.height).inches:.2f}" for r in tbl.rows]
                    lines.append(f"    row heights(in)={heights}")
                except Exception:  # noqa: BLE001
                    pass
                for ri, row in enumerate(tbl.rows):
                    for ci, cell in enumerate(row.cells):
                        txt = cell.text.strip()
                        if not txt:
                            continue
                        lines.append(f"    [r{ri}c{ci}]")
                        lines.extend(dump_cell(cell, "      "))
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
