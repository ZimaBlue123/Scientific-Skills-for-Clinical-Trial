"""Move 4 scripts to scripts/_archive_2026_consolidation/ (Python — more reliable than cmd move for unicode paths)."""
import shutil
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
SRC = ROOT / "scripts"
DST = ROOT / "scripts" / "_archive_2026_consolidation"

DST.mkdir(parents=True, exist_ok=True)

moves = [
    "_extract_docx_text.py",
    "extract_docx_to_md.py",
    "convert_doc_to_docx.py",
    "convert_audit_report_md_to_docx.py",
]

for name in moves:
    src = SRC / name
    dst = DST / name
    if not src.exists():
        print(f"SKIP (not found): {src}")
        continue
    if dst.exists():
        print(f"SKIP (already archived): {dst}")
        continue
    shutil.move(str(src), str(dst))
    print(f"MOVED: {src.name}")

print()
print("Archive contents:")
for p in sorted(DST.iterdir()):
    print(f"  {p.name} ({p.stat().st_size} bytes)")

print()
print("scripts/ remaining *.py:")
for p in sorted(SRC.glob("*.py")):
    print(f"  {p.name}")