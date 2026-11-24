"""PPTX table layout QA via PowerPoint COM (Windows only).

For every table cell the ACTUAL rendered text height
(``TextFrame2.TextRange.BoundHeight``) is compared with the cell height. A
positive overflow means the viewer will grow that row, so any free-standing
textbox placed under the table (e.g. a conclusion box) may be overlapped in
WPS / PowerPoint. Each table's bottom edge is also checked against a limit.

Usage::

    python scripts/pipeline/validate/pptx_overflow_checker.py deck.pptx [--max-bottom 6.27]

Exit code: 0 = PASS, 1 = layout issues found, 2 = input / COM error.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

PT_PER_INCH = 72.0
DEFAULT_MAX_BOTTOM_IN = 6.27
OVERFLOW_TOLERANCE_PT = 1.0


@dataclass
class TableReport:
    slide: int
    rows: int
    bottom_in: float
    overflow_cells: list[str] = field(default_factory=list)
    skipped_cells: int = 0  # merged / COM-inaccessible cells that could not be measured


def check_pptx_overflow(
    pptx_path: str | Path,
    max_bottom_in: float = DEFAULT_MAX_BOTTOM_IN,
    tolerance_pt: float = OVERFLOW_TOLERANCE_PT,
) -> tuple[list[TableReport], list[str]]:
    """Return ``(table_reports, issues)`` for every table in ``pptx_path``."""
    path = Path(pptx_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    import win32com.client  # local import: Windows/pywin32 only

    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = None
    reports: list[TableReport] = []
    issues: list[str] = []
    try:
        pres = app.Presentations.Open(str(path), ReadOnly=True, WithWindow=False)
        for i, slide in enumerate(pres.Slides, 1):
            for sh in slide.Shapes:
                if not sh.HasTable:
                    continue
                bottom = (sh.Top + sh.Height) / PT_PER_INCH
                tbl = sh.Table
                rep = TableReport(slide=i, rows=tbl.Rows.Count, bottom_in=bottom)
                if bottom > max_bottom_in:
                    issues.append(f"P{i:02d} table bottom {bottom:.3f} > {max_bottom_in:.3f}")
                for r in range(1, tbl.Rows.Count + 1):
                    for c in range(1, tbl.Columns.Count + 1):
                        try:
                            cell = tbl.Cell(r, c)
                            rng = cell.Shape.TextFrame2.TextRange
                            if not rng.Text.strip():
                                continue
                            excess = rng.BoundHeight - cell.Shape.Height
                        except Exception:  # merged / inaccessible cells
                            rep.skipped_cells += 1
                            continue
                        if excess > tolerance_pt:
                            rep.overflow_cells.append(f"R{r}C{c} +{excess:.1f}pt")
                if rep.overflow_cells:
                    issues.append(f"P{i:02d} overflow: {', '.join(rep.overflow_cells[:8])}")
                reports.append(rep)
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()
    return reports, issues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pptx", help="Path to the .pptx file")
    ap.add_argument("--max-bottom", type=float, default=DEFAULT_MAX_BOTTOM_IN,
                    help="Maximum allowed table bottom in inches (default %(default)s)")
    args = ap.parse_args(argv)

    try:
        reports, issues = check_pptx_overflow(args.pptx, args.max_bottom)
    except FileNotFoundError as exc:
        print(f"ERROR: file not found: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # COM / pywin32 failures
        print(f"ERROR: PowerPoint COM failure: {exc}", file=sys.stderr)
        return 2

    for rep in reports:
        cells = ", ".join(rep.overflow_cells[:8]) or "none"
        skipped = f"  skipped_cells={rep.skipped_cells}" if rep.skipped_cells else ""
        print(f"P{rep.slide:02d}  rows={rep.rows}  bottom={rep.bottom_in:.3f}in  overflow_cells={cells}{skipped}")
    print()
    if issues:
        print("!! ISSUES:")
        for line in issues:
            print("  ", line)
        return 1
    print(f"PASS: no cell text overflow, all table bottoms <= {args.max_bottom:.3f}in")
    return 0


if __name__ == "__main__":
    sys.exit(main())
