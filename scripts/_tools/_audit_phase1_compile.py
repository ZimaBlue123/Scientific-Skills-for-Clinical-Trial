#!/usr/bin/env python3
"""阶段 1-2: py_compile 全量编译 + AST 语法树解析。"""
from __future__ import annotations
import ast
import pathlib
import py_compile
import sys

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIST = ROOT / "reports" / "phase1_file_list.txt"
OUT_OK = ROOT / "reports" / "phase1_compile_ok.txt"
OUT_FAIL = ROOT / "reports" / "phase1_compile_fail.txt"


def main() -> int:
    files = [ROOT / line.strip() for line in LIST.read_text(encoding="utf-8").splitlines() if line.strip()]
    ok: list[str] = []
    fail: list[tuple[str, str]] = []
    ast_fail: list[tuple[str, str]] = []
    for p in files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        # py_compile
        try:
            py_compile.compile(str(p), doraise=True)
            ok.append(rel)
        except py_compile.PyCompileError as exc:
            fail.append((rel, str(exc).splitlines()[0]))
        except Exception as exc:
            fail.append((rel, f"{type(exc).__name__}: {exc}"))
        # AST parse (independent of py_compile, catches subtle issues)
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="ignore"), filename=rel)
        except SyntaxError as exc:
            ast_fail.append((rel, f"SyntaxError L{exc.lineno}: {exc.msg}"))
    OUT_OK.write_text("\n".join(ok) + "\n", encoding="utf-8")
    OUT_FAIL.write_text("\n".join(f"{r}\t{err}" for r, err in fail + ast_fail) + "\n", encoding="utf-8")
    print(f"COMPILED={len(ok)}")
    print(f"COMPILE_FAILED={len(fail)}")
    print(f"AST_FAILED={len(ast_fail)}")
    for rel, err in fail + ast_fail:
        print(f"  FAIL  {rel}: {err}")
    return 0 if not (fail or ast_fail) else 1


if __name__ == "__main__":
    sys.exit(main())