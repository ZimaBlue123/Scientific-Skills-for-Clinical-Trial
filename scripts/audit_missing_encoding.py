#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_missing_encoding.py

审计仓库脚本中「读写文本但未显式指定 encoding」的 open() / Path.open() 调用。

背景
----
Windows zh-CN 环境的默认 ANSI 代码页是 CP936(GBK)。读写文件时不写
encoding="utf-8"，Python 就会用 locale 默认编码（Windows 上通常是 cp936），
把 UTF-8 的中文按 GBK 解码再存回，产生不可逆的乱码（本仓库 README.md
曾因此损坏，见 commit 7eb7ed4）。

判定规则
--------
- 仅审计文本读写：mode 不含 "b"，或 mode 缺省（即 "r"）。
- 已带 encoding= 关键字参数的调用视为合规，跳过。
- 命中即报告 文件:行号 与调用片段，供人工确认。

用法:
    python scripts/audit_missing_encoding.py [根目录]
    python scripts/audit_missing_encoding.py --json          # 输出 JSON
"""

from __future__ import annotations

import ast
import json
import os
import sys

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".workbuddy"}

# 第三方库的 .open() 不是文件文本读写，须排除，否则大量误报
# （Image.open / fitz.open / pdfplumber.open / io.BytesIO 等）
LIB_RECEIVERS = {
    "fitz", "Image", "pdfplumber", "PIL", "pypdf", "PyPDF2", "io",
    "soundfile", "wave", "zipfile", "tarfile", "Document", "PdfReader",
    "pptx", "docx", "workbook", "pdf", "img",
}


def is_builtin_open(node: ast.Call) -> bool:
    fn = node.func
    return isinstance(fn, ast.Name) and fn.id == "open"


def is_path_open(node: ast.Call) -> bool:
    """Path.open(...) / path.open(...)。排除第三方库的同名方法。"""
    fn = node.func
    if not (isinstance(fn, ast.Attribute) and fn.attr == "open"):
        return False
    recv = fn.value
    if isinstance(recv, ast.Name):
        if recv.id in LIB_RECEIVERS:
            return False
        # 首字母大写的通常是类（如 Image.open / Document.open）
        if recv.id[:1].isupper():
            return False
        return True
    # io.BytesIO(...) 之类：接收者是调用表达式，按库调用排除
    return False


def mode_of(call: ast.Call) -> str | None:
    """返回 mode 字面量；缺省视为 'r'。"""
    for kw in call.keywords:
        if kw.arg == "mode":
            if isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
            return None
    # 位置参数里找 mode 字面量：
    #   open(path, "w")     -> args[1]
    #   Path(path).open("w")-> args[0]
    for idx in (1, 0):
        if len(call.args) > idx and isinstance(call.args[idx], ast.Constant):
            v = call.args[idx].value
            if isinstance(v, str) and v in {"r", "w", "a", "x", "rb", "wb"}:
                return v
    return "r"


def has_encoding(call: ast.Call) -> bool:
    return any(kw.arg == "encoding" for kw in call.keywords)


def scan_file(path: str) -> list[dict]:
    try:
        src = open(path, "r", encoding="utf-8").read()
        tree = ast.parse(src, filename=path)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    hits: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (is_builtin_open(node) or is_path_open(node)):
            continue
        if has_encoding(node):
            continue
        mode = mode_of(node)
        if mode is None or "b" in mode:  # 无法判定或二进制模式，跳过
            continue
        seg = ast.get_source_segment(src, node) or ""
        hits.append(
            {"line": node.lineno, "call": " ".join(seg.split())[:90]}
        )
    return hits


def main() -> int:
    args = [a for a in sys.argv[1:]]
    as_json = "--json" in args
    args = [a for a in args if not a.startswith("--")]
    root = args[0] if args else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    report: dict[str, list[dict]] = {}
    files = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            files += 1
            hits = scan_file(full)
            if hits:
                report[os.path.relpath(full, root).replace("\\", "/")] = hits

    total = sum(len(v) for v in report.values())
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"审计 .py 文件 {files} 个，命中文件 {len(report)} 个，"
          f"未指定 encoding 的调用 {total} 处")
    print("-" * 78)
    for rel in sorted(report):
        print(f"\n{rel}")
        for h in report[rel]:
            print(f"  L{h['line']:>4}  {h['call']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
