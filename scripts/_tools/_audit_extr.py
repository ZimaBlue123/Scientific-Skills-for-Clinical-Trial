"""Compare extract_* scripts at the function/class level."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
files = [
    "scripts/_extract_docx_text.py",
    "scripts/extract_doc_text.py",
    "scripts/extract_docx_full.py",
    "scripts/extract_docx_to_md.py",
    "scripts/extract_ib_texts.py",
]
for f in files:
    p = ROOT / f
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:
        print(f"{f}: PARSE ERROR {e}")
        continue
    fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    cls = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    print(f"{f}:")
    print(f"  functions: {fns[:8]}{'...' if len(fns)>8 else ''}")
    print(f"  classes:   {cls}")
    print()