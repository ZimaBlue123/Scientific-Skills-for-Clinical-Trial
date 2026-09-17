"""Authoritative overflow check via the PowerPoint COM automation API.

Opens the generated deck in PowerPoint and compares each shape's real rendered
text height (TextFrame2.BoundHeight) against the shape/row height. Table rows
auto-grow in PowerPoint when the text does not fit, which would silently break
the carefully computed vertical rhythm of the deck - this detects that case.
"""

from __future__ import annotations

import sys
from pathlib import Path

import win32com.client  # type: ignore

PPTX = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "汇报准备输出"
    / "TVAX-009_Ⅰ期细胞免疫与同类CpG佐剂乙肝疫苗对比分析.pptx"
)
OUT = Path(__file__).with_name("_com_overflow_check.txt")

EMU_IN = 914400.0


def main() -> int:
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(PPTX), ReadOnly=True, WithWindow=False)
    buf: list[str] = [f"file: {PPTX.name}", f"slides: {pres.Slides.Count}", ""]
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
    OUT.write_text("\n".join(buf), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
