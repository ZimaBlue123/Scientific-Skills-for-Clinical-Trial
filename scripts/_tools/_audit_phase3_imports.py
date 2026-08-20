#!/usr/bin/env python3
"""阶段 3-2: 扫描所有 scripts/ + skills/ 的 import，生成依赖使用矩阵。"""
from __future__ import annotations

import ast
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIST = ROOT / "reports" / "phase1_file_list.txt"
OUT = ROOT / "reports" / "phase3_imports.md"

# stdlib module names（3.10+）
STDLIB = {
    "abc", "argparse", "ast", "asyncio", "base64", "bisect", "builtins", "bz2",
    "calendar", "collections", "contextlib", "copy", "csv", "ctypes", "dataclasses",
    "datetime", "decimal", "difflib", "enum", "errno", "fnmatch", "functools",
    "gc", "getopt", "getpass", "glob", "gzip", "hashlib", "heapq", "html",
    "http", "importlib", "inspect", "io", "itertools", "json", "logging",
    "math", "mimetypes", "multiprocessing", "numbers", "operator", "os",
    "pathlib", "pickle", "platform", "posixpath", "pprint", "queue", "random",
    "re", "shutil", "signal", "socket", "sqlite3", "ssl", "stat", "string",
    "subprocess", "sys", "tempfile", "textwrap", "threading", "time", "tokenize",
    "traceback", "types", "typing", "unicodedata", "unittest", "urllib", "uuid",
    "venv", "warnings", "weakref", "xml", "zipfile", "zlib",
    "collections.abc", "concurrent", "concurrent.futures", "ctypes",
    "tkinter", "typing_extensions",
}

# 已声明在 requirements.txt 的库
DECLARED = {
    "docx",  # python-docx
    "pptx",  # python-pptx
    "fitz", "pymupdf",
    "pypdf",
    "pdfplumber",
    "striprtf",
    "markitdown",
    "win32com", "win32com.client", "pythoncom",  # pywin32
    "PIL",  # Pillow
    "pytesseract",
    "img2table",
    "cv2",  # opencv-contrib-python-headless
    "bs4",  # beautifulsoup4
    "openpyxl",
    "olefile",
    "numpy",
    "pandas",
    "statsmodels",
    "matplotlib", "matplotlib.pyplot",
    "lifelines",
    "cairosvg",
    "openai",
}

DEV_DECLARED = {
    "flake8", "pytest", "ruff", "mypy", "pre_commit",
}


def main() -> int:
    files = [ROOT / l.strip() for l in LIST.read_text(encoding="utf-8").splitlines() if l.strip()]
    # import_name -> set of importing files
    usage: dict[str, set[str]] = defaultdict(set)
    for p in files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"), filename=str(p))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    usage[name].add(str(p.relative_to(ROOT)).replace("\\", "/"))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    usage[top].add(str(p.relative_to(ROOT)).replace("\\", "/"))
    # Classify.
    third_party_used: Counter[str] = Counter()
    third_party_undeclared: list[tuple[str, int]] = []
    stdlib_used = 0
    for name, callers in usage.items():
        if name in STDLIB:
            stdlib_used += 1
            continue
        n = len(callers)
        third_party_used[name] = n
        if name not in DECLARED and name not in DEV_DECLARED:
            third_party_undeclared.append((name, n))
    # Write markdown.
    lines = [
        "# 阶段 3-2: Import 依赖审计",
        "",
        f"扫描: {len(files)} 个文件",
        f"stdlib 模块: {stdlib_used} 个",
        f"第三方模块（已声明 + 未声明）: {len(third_party_used)} 个",
        f"未声明的第三方模块: {len(third_party_undeclared)} 个",
        "",
        "## 未声明的第三方模块",
        "",
        "下列模块在脚本中被 import，但**未在 requirements.txt 中声明**。可能原因：",
        "1. 模块已包含在已声明的更大包的子模块中（如 PIL 已在 Pillow 里）",
        "2. 是 typo 或遗留 import",
        "3. 是 stdlib 重新导出（误判）",
        "4. 真的遗漏",
        "",
        "| 模块 | 使用文件数 | 类别判定 |",
        "|---|---:|---|",
    ]
    likely_subsumed = {"PIL", "win32com", "win32com.client", "pythoncom", "fitz", "bs4", "matplotlib"}
    likely_dev = {"logging.config"}  # dev/optional
    for name, n in sorted(third_party_undeclared, key=lambda kv: -kv[1]):
        if name in likely_subsumed:
            kind = "已包含（子模块）"
        elif name in likely_dev:
            kind = "stdlib 误判"
        elif name.startswith("_") or len(name) <= 2:
            kind = "内部 / typo"
        else:
            kind = "需检查"
        lines.append(f"| `{name}` | {n} | {kind} |")
    lines.extend([
        "",
        "## 已声明第三方模块（按使用频次排序）",
        "",
        "| 模块 | 使用文件数 |",
        "|---|---:|",
    ])
    for name, n in sorted(third_party_used.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{name}` | {n} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WRITTEN={OUT}")
    print(f"UNUSED_DECLARED={[n for n in DECLARED if n not in usage]}")
    print(f"UNDECLARED_THIRD_PARTY={len(third_party_undeclared)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())