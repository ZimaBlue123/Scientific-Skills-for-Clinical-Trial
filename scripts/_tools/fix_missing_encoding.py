#!/usr/bin/env python
"""
fix_missing_encoding.py

给「读写文本但未指定 encoding」的 open() / Path.open() 调用自动补上
encoding="utf-8"。

为什么需要
----------
Windows zh-CN 默认 ANSI 代码页是 CP936(GBK)。不写 encoding 时 Python 用
locale 默认编码读写，会把 UTF-8 中文按 GBK 解码再存回，造成不可逆乱码。
本仓库 README.md 就曾因此损坏（commit 7eb7ed4）。

实现方式
--------
用 ast 定位调用，再按 node.end_lineno / end_col_offset 精确定位右括号位置，
在源码字节级别插入参数 —— 不做正则替换，避免破坏嵌套表达式。
插入前会判断右括号前是否已有逗号，避免产生 `,,`。
跳过含 `**` 解包的调用（无法确定参数安全性）。

安全机制
--------
- 默认 dry-run，只报告；显式 `--apply` 才写盘。
- 写盘前后都做 py_compile 校验，任一文件语法不合法即整体中止。

用法:
    python scripts/fix_missing_encoding.py                  # dry-run
    python scripts/fix_missing_encoding.py --apply          # 实际修改
    python scripts/fix_missing_encoding.py skills/ --apply  # 限定目录
"""

from __future__ import annotations

import ast
import os
import py_compile
import sys
import tempfile

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".workbuddy"}
LIB_RECEIVERS = {
    "fitz",
    "Image",
    "pdfplumber",
    "PIL",
    "pypdf",
    "PyPDF2",
    "io",
    "soundfile",
    "wave",
    "zipfile",
    "tarfile",
    "Document",
    "PdfReader",
    "pptx",
    "docx",
    "workbook",
    "pdf",
    "img",
}
INSERT = b'encoding="utf-8"'


def is_target(call: ast.Call) -> bool:
    fn = call.func
    if isinstance(fn, ast.Name):
        return fn.id == "open"
    if isinstance(fn, ast.Attribute) and fn.attr == "open":
        recv = fn.value
        if isinstance(recv, ast.Name):
            return recv.id not in LIB_RECEIVERS and not recv.id[:1].isupper()
    return False


def has_encoding(call: ast.Call) -> bool:
    return any(kw.arg == "encoding" for kw in call.keywords)


def mode_has_b(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return "b" in str(kw.value.value)
    for idx in (1, 0):
        if len(call.args) > idx and isinstance(call.args[idx], ast.Constant):
            v = call.args[idx].value
            if isinstance(v, str) and "b" in v:
                return True
    return False


def has_starstar(call: ast.Call) -> bool:
    return any(isinstance(a, ast.Starred) for a in call.args) or any(
        kw.arg is None for kw in call.keywords
    )


def collect(path: str) -> list[ast.Call]:
    try:
        raw = open(path, "rb").read()
        tree = ast.parse(raw, filename=path)
    except (SyntaxError, OSError, ValueError):
        return []
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not is_target(node):
            continue
        if has_encoding(node) or mode_has_b(node) or has_starstar(node):
            continue
        if node.end_lineno is None or node.end_col_offset is None:
            continue
        out.append(node)
    return out


def prev_nonspace(lines: list[bytes], lineno0: int, col: int) -> bytes:
    """从 (lineno0, col) 位置向前找第一个非空白字节（可跨行）。"""
    i, j = lineno0, col
    while i >= 0:
        line = lines[i]
        while j > 0:
            b = line[j - 1 : j]
            if b not in (b" ", b"\t", b"\r"):
                return b
            j -= 1
        i -= 1
        if i < 0:
            break
        j = len(lines[i])
    return b""


def patch_source(raw: bytes, calls: list[ast.Call]) -> tuple[bytes, int]:
    lines = raw.split(b"\n")
    # 从后往前改，避免插入后偏移影响后续定位
    for node in sorted(calls, key=lambda n: (n.end_lineno, n.end_col_offset), reverse=True):
        i = node.end_lineno - 1
        idx = node.end_col_offset - 1  # 右括号下标
        line = lines[i]
        if idx < 0 or line[idx : idx + 1] != b")":
            continue
        need_comma = prev_nonspace(lines, i, idx) != b","
        ins = (b", " if need_comma else b" ") + INSERT
        lines[i] = line[:idx] + ins + line[idx:]
    return b"\n".join(lines), len(calls)


def compile_ok(path: str, raw: bytes) -> bool:
    """用临时文件做 py_compile 校验，不改动原文件。"""
    fd, tmp = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
        py_compile.compile(tmp, cfile=tmp + "c", doraise=True)
        return True
    except Exception:
        return False
    finally:
        for p in (tmp, tmp + "c"):
            if os.path.exists(p):
                os.remove(p)


def main() -> int:
    argv = sys.argv[1:]
    apply_changes = "--apply" in argv
    paths = [a for a in argv if not a.startswith("--")]
    root = paths[0] if paths else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    changed_files, changed_calls = 0, 0
    failed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            calls = collect(full)
            if not calls:
                continue
            raw = open(full, "rb").read()
            new_raw, n = patch_source(raw, calls)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if not compile_ok(full, new_raw):
                print(f"  [跳过] {rel}  补丁后语法校验失败")
                failed += 1
                continue
            changed_files += 1
            changed_calls += n
            if apply_changes:
                with open(full, "wb") as fh:
                    fh.write(new_raw)
                print(f"  [已改] {rel}  +{n}")
            else:
                print(f"  [待改] {rel}  +{n}")

    verb = "已修改" if apply_changes else "待修改(dry-run)"
    print(f"\n{verb} 文件 {changed_files} 个，调用 {changed_calls} 处；校验失败 {failed} 个")
    if not apply_changes:
        print("确认无误后加 --apply 执行写盘。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
