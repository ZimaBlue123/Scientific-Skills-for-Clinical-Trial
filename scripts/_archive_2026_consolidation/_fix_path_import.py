"""Add missing 'from pathlib import Path' to docx_utils.py and self-check."""
import subprocess
import sys
from pathlib import Path as P

target = P(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts\common_scripts\docx_utils.py")
src = target.read_text(encoding="utf-8")

OLD = """import logging
from collections.abc import Iterable

from docx import Document
from docx.oxml.ns import qn
"""

NEW = """import logging
from collections.abc import Iterable
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
"""

if OLD not in src:
    print("FATAL: OLD import block not found - manual fix needed")
    sys.exit(1)

if "from pathlib import Path" in src:
    print("ALREADY FIXED: Path import already present")
else:
    src = src.replace(OLD, NEW)
    target.write_text(src, encoding="utf-8")
    print(f"FIXED: added 'from pathlib import Path' to {target}")

# Self-check 1: py_compile
print("\n=== py_compile ===")
res = subprocess.run([sys.executable, "-m", "py_compile", str(target)], capture_output=True, text=True)
print("rc:", res.returncode)
if res.stderr:
    print("stderr:", res.stderr)
print("OK" if res.returncode == 0 else "FAIL")

# Self-check 2: AST-based undefined name check (mimic pyflakes F821)
print("\n=== AST undefined-name check ===")
import ast
tree = ast.parse(src)
imported = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            imported.add(n.asname or n.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom):
        for n in node.names:
            imported.add(n.asname or n.name)
# also collect builtins to ignore
import builtins
defined_names = set(dir(builtins)) | imported | {"__name__", "__file__", "__doc__"}

# Walk tree collecting Name nodes
undefined: list[str] = []
for node in ast.walk(tree):
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        if node.id not in defined_names:
            undefined.append(node.id)
print("Undefined names:", undefined if undefined else "(none)")
if "Path" in undefined:
    print("FAIL: 'Path' still undefined")
    sys.exit(1)
else:
    print("PASS: 'Path' resolved or not used at module level")

# Self-check 3: explicit definition lookup in source
print("\n=== Direct grep for 'Path' usage ===")
import re
for i, line in enumerate(src.splitlines(), 1):
    if "Path(" in line or re.search(r"\bPath\b", line):
        print(f"  L{i}: {line.rstrip()[:80]}")