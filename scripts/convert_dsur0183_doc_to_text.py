#!/usr/bin/env python3
"""Convert the DSUR#2 draft (.doc, legacy binary) to .docx + Markdown/JSON.

Uses the local Word COM automation (Windows only) to open the legacy .doc and
re-save it as .docx, then delegates text/table extraction to scripts/convert_to_md.py.

Usage
-----
    py -3 scripts/convert_dsur0183_doc_to_text.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "review_materials" / "018-3"
WORK_DIR = SRC_DIR / "_work"

DOC_NAME = "远大赛威信_重组破伤风疫苗（大肠埃希菌）_DSUR#2（20250812-20260811）-初稿.doc"


def doc_to_docx(src: Path, dst: Path) -> Path:
    """Re-save a legacy .doc as .docx through Word COM."""
    import win32com.client  # type: ignore

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        document = word.Documents.Open(str(src), ReadOnly=True)
        try:
            # 16 = wdFormatDocumentDefault (.docx)
            document.SaveAs2(str(dst), FileFormat=16)
        finally:
            document.Close(False)
    finally:
        word.Quit()
    return dst


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    src = SRC_DIR / DOC_NAME
    if not src.exists():
        print(f"SOURCE NOT FOUND: {src}")
        return 2

    # keep an ASCII alias because some toolchains choke on CJK paths
    alias_doc = WORK_DIR / "dsur_input.doc"
    alias_docx = WORK_DIR / "dsur_input.docx"
    shutil.copy2(src, alias_doc)

    if not alias_docx.exists():
        doc_to_docx(alias_doc, alias_docx)
    print(f"docx -> {alias_docx}")

    converter = ROOT / "scripts" / "convert_to_md.py"
    out_md = WORK_DIR / "dsur_numbered.md"
    cmd = [sys.executable, str(converter), str(alias_docx), "-o", str(out_md), "--mode", "numbered"]
    print(" ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout[-3000:])
    print(res.stderr[-3000:])
    if not out_md.exists():
        return 3

    # also dump a structured dump (paragraphs + tables) for fine-grained checks
    dump_cmd = [sys.executable, str(ROOT / "scripts" / "dump_dsur0183_structure.py")]
    subprocess.run(dump_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    print(json.dumps({"md": str(out_md), "docx": str(alias_docx)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
