"""Detect overlapping functionality in scripts/ via shared imports."""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts")

EXTRACT_DIRS = {"scripts"}  # only top-level scripts/


def imports_of(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                out.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module.split(".")[0])
    return out


def main():
    by_import: dict[str, list[str]] = defaultdict(list)
    for p in sorted(ROOT.rglob("*.py")):
        if "_archive" in p.parts or "__pycache__" in p.parts:
            continue
        imps = imports_of(p)
        rel = str(p.relative_to(ROOT.parent)).replace("\\", "/")
        for imp in imps:
            by_import[imp].append(rel)

    print("=== 共享第三方库分布（按 import 数量排序） ===")
    third_party = {"docx", "pptx", "openpyxl", "fitz", "pdfplumber", "striprtf", "PIL",
                   "pytesseract", "img2table", "cv2", "requests", "bs4", "pandas",
                   "numpy", "matplotlib", "lxml", "yaml", "rich"}
    for imp in sorted(by_import, key=lambda k: -len(by_import[k])):
        files = by_import[imp]
        if imp in third_party or imp.startswith("scripts."):
            print(f"  {imp:25s} : {len(files):2d} scripts")
            for f in files:
                print(f"      - {f}")


if __name__ == "__main__":
    main()