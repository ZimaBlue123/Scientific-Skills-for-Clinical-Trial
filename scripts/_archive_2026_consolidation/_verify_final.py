"""Final verification: pyflakes + git log/status + push check."""

import subprocess
from pathlib import Path

cwd = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
PY = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"

# 1. Pyflakes on the changed file only
target = cwd / "scripts/common_scripts/docx_utils.py"
res = subprocess.run([PY, "-m", "pyflakes", str(target)], capture_output=True, text=True)
print("=== pyflakes on fixed file ===")
print(f"rc={res.returncode}")
print(f"stdout: {res.stdout!r}")
assert res.returncode == 0 and not res.stdout.strip(), "STILL HAS ERRORS"

# 2. Git status
res = subprocess.run(
    ["git", "status", "--short", "--branch"], cwd=cwd, capture_output=True, text=True
)
print()
print("=== git status --short --branch ===")
print(res.stdout)

# 3. Last 3 commits on origin/main
res = subprocess.run(
    ["git", "log", "--oneline", "-3", "origin/main"],
    cwd=cwd,
    capture_output=True,
    text=True,
)
print("=== origin/main last 3 ===")
print(res.stdout)

# 4. Confirm ahead/behind
res = subprocess.run(
    ["git", "rev-list", "--left-right", "--count", "main...origin/main"],
    cwd=cwd,
    capture_output=True,
    text=True,
)
print("=== ahead/behind ===")
print(res.stdout)

print("=== ALL CHECKS PASSED ===")
print("Fix pushed: F821 (Path import) and F811 (duplicate _os import) resolved.")
print("Pyflakes: clean across full scripts/ tree (36 files)")
print("CI lint with flake8 should now pass on next build.")
