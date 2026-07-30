"""Run pyflakes over the entire scripts/ tree (excluding _archive)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts")
PY = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"

errors: list[str] = []
total = 0
for p in sorted(ROOT.rglob("*.py")):
    if "_archive" in p.parts or "__pycache__" in p.parts:
        continue
    if p.name.startswith("selftest"):
        continue
    total += 1
    res = subprocess.run([PY, "-m", "pyflakes", str(p)], capture_output=True, text=True)
    if res.returncode != 0 and res.stdout.strip():
        errors.append(f"{p.relative_to(ROOT.parent)}:\n{res.stdout.rstrip()}")

print(f"Checked {total} Python files")
if errors:
    print(f"\n=== {len(errors)} files with pyflakes issues ===\n")
    for e in errors:
        print(e)
        print()
else:
    print("\nALL CLEAN: no pyflakes issues across scripts/ (excluding _archive and _selftest_*)")
sys.exit(1 if errors else 0)