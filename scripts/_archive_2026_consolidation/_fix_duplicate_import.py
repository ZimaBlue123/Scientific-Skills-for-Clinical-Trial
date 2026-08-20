"""Remove duplicate 'import os as _os' in docx_utils.py."""

from pathlib import Path

p = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts\common_scripts\docx_utils.py"
)
src = p.read_text(encoding="utf-8")

# Remove the SECOND redundant import (L136 in current file)
OLD = """    import os as _os  # local alias keeps the rest of this function self-contained

    pythoncom.CoInitialize()"""

NEW = """    pythoncom.CoInitialize()"""

if OLD not in src:
    print("FATAL: duplicate import block not found")
    import sys

    sys.exit(1)

src = src.replace(OLD, NEW)
p.write_text(src, encoding="utf-8")
print(f"FIXED: removed duplicate import os as _os in {p}")
print(f"New size: {p.stat().st_size} bytes")

# Re-run pyflakes
import subprocess

res = subprocess.run(
    [
        "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
        "-m",
        "pyflakes",
        str(p),
    ],
    capture_output=True,
    text=True,
)
print()
print("=== pyflakes output ===")
print(res.stdout or "(empty)")
print("rc:", res.returncode)
