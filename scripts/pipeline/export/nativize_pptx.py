"""Normalize a python-pptx output by round-tripping it through PowerPoint COM.

Constraint (workspace policy): all generated .py must live under ``scripts/``.

python-pptx output is "close enough" but not PowerPoint-native serialization;
opening + SaveAs2 through PowerPoint guarantees PowerPoint can re-open its own
file, and drops orphan slide parts left behind by deleted slides.

Usage:
    python scripts/nativize_pptx.py stage.pptx final.pptx
"""

from __future__ import annotations

import argparse
from pathlib import Path

PP_SAVEAS_OPENXML_PRESENTATION = 24  # ppSaveAsOpenXMLPresentation


def nativize(stage: Path, final: Path) -> int:
    import win32com.client as win32

    stage, final = Path(stage).resolve(), Path(final).resolve()
    app = win32.gencache.EnsureDispatch("PowerPoint.Application")
    try:
        pres = app.Presentations.Open(str(stage), ReadOnly=False, Untitled=False, WithWindow=False)
        try:
            n = pres.Slides.Count
            if final.exists():
                final.unlink()
            pres.SaveAs(str(final), PP_SAVEAS_OPENXML_PRESENTATION)
            size = final.stat().st_size
            print(f"OK slides={n} size={size/1024/1024:.2f} MB -> {final}")
        finally:
            pres.Close()
    finally:
        app.Quit()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("final")
    args = ap.parse_args()
    return nativize(Path(args.stage), Path(args.final))


if __name__ == "__main__":
    raise SystemExit(main())
