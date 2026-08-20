#!/usr/bin/env python3
"""阶段 1-4: AST 深度审查 — bare except、type hint、logging、异常捕获。"""
from __future__ import annotations

import ast
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIST = ROOT / "reports" / "phase1_file_list.txt"
OUT_MD = ROOT / "reports" / "phase1_ast_audit.md"


def scan(path: pathlib.Path) -> dict:
    """Return per-file metrics."""
    src = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return {"error": "SyntaxError"}
    metrics = {
        "lines": src.count("\n") + 1,
        "funcs": 0,
        "funcs_with_return_hint": 0,
        "funcs_no_returnHint": [],
        "funcs_with_logging": 0,
        "funcs_with_try": 0,
        "funcs_with_bare_except": [],
        "funcs_with_pass": 0,
        "module_has_logger": False,
        "excepthandlers": 0,
        "bare_excepthandlers": 0,
        "broad_excepthandlers": [],
        "prints": 0,
        "file_path": str(path.relative_to(ROOT)).replace("\\", "/"),
    }
    # Module-level logger presence.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in {"LOGGER", "logger", "_logger"}:
                    metrics["module_has_logger"] = True
        if isinstance(node, ast.FunctionDef):
            metrics["funcs"] += 1
            has_hint = node.returns is not None
            if has_hint:
                metrics["funcs_with_return_hint"] += 1
            else:
                metrics["funcs_no_returnHint"].append(node.name)
            # Walk body for logging / try / pass / bare except / print.
            has_log = False
            has_try = False
            has_bare = False
            has_pass_only = False
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    fn = sub.func
                    if isinstance(fn, ast.Attribute):
                        if fn.attr in {"info", "warning", "error", "debug", "exception"}:
                            has_log = True
                    elif isinstance(fn, ast.Name) and fn.id in {"print", "warn", "log"}:
                        pass
                if isinstance(sub, ast.Try):
                    has_try = True
                    for h in sub.handlers:
                        metrics["excepthandlers"] += 1
                        if h.type is None:
                            metrics["bare_excepthandlers"] += 1
                            has_bare = True
                        else:
                            # broad exception = Exception or BaseException
                            if isinstance(h.type, ast.Name) and h.type.id in {"Exception", "BaseException"}:
                                metrics["broad_excepthandlers"].append(h.type.id)
                if isinstance(sub, ast.ExceptHandler) and sub.type is None:
                    has_bare = True
                if isinstance(sub, ast.Pass):
                    # Only count if function body is essentially just pass (i.e. placeholder)
                    pass
            if has_log:
                metrics["funcs_with_logging"] += 1
            if has_try:
                metrics["funcs_with_try"] += 1
            if has_bare:
                metrics["funcs_with_bare_except"].append(node.name)
        if isinstance(node, ast.ExceptHandler):
            metrics["excepthandlers"] += 1
            if node.type is None:
                metrics["bare_excepthandlers"] += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            metrics["prints"] += 1
    return metrics


def main() -> int:
    files = [ROOT / line.strip() for line in LIST.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows: list[dict] = []
    for p in files:
        try:
            m = scan(p)
            if "error" in m:
                continue
            rows.append(m)
        except Exception as exc:
            print(f"SKIP {p}: {exc}", file=sys.stderr)
    # Aggregate.
    total_funcs = sum(r["funcs"] for r in rows)
    funcs_with_hint = sum(r["funcs_with_return_hint"] for r in rows)
    funcs_with_log = sum(r["funcs_with_logging"] for r in rows)
    funcs_with_try = sum(r["funcs_with_try"] for r in rows)
    total_except = sum(r["excepthandlers"] for r in rows)
    bare_except = sum(r["bare_excepthandlers"] for r in rows)
    files_with_bare = sum(1 for r in rows if r["bare_excepthandlers"] > 0)
    files_no_logger = sum(1 for r in rows if not r["module_has_logger"] and r["funcs"] > 3)
    files_with_prints = sum(1 for r in rows if r["prints"] > 0)
    total_prints = sum(r["prints"] for r in rows)
    # Write summary.
    md = [
        "# Phase 1-4: AST 深度审查",
        "",
        f"扫描: {len(rows)} 个文件",
        "",
        "## 汇总指标",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 函数总数 | {total_funcs} |",
        f"| 有返回类型注解的函数 | {funcs_with_hint} ({funcs_with_hint * 100 // max(total_funcs, 1)}%) |",
        f"| 调用 logger 的函数 | {funcs_with_log} ({funcs_with_log * 100 // max(total_funcs, 1)}%) |",
        f"| 含 try 块的函数 | {funcs_with_try} ({funcs_with_try * 100 // max(total_funcs, 1)}%) |",
        f"| except handler 总数 | {total_except} |",
        f"| bare except 数 | {bare_except} |",
        f"| 含 bare except 的文件数 | {files_with_bare} |",
        f"| 含 broad Exception/BaseException 的文件数 | {sum(1 for r in rows if r['broad_excepthandlers'])} |",
        f"| 模块级 logger 缺失的文件数 (>3 函数) | {files_no_logger} |",
        f"| 使用 print() 的文件数 | {files_with_prints} |",
        f"| print() 总调用数 | {total_prints} |",
        "",
        "## Top 10: bare except 文件",
        "",
        "| 文件 | 函数 | bare 数 |",
        "|---|---|---:|",
    ]
    rows_bare = [r for r in rows if r["bare_excepthandlers"] > 0]
    rows_bare.sort(key=lambda r: -r["bare_excepthandlers"])
    for r in rows_bare[:10]:
        funcs = ", ".join(r["funcs_with_bare_except"][:3])
        if len(r["funcs_with_bare_except"]) > 3:
            funcs += f" ... (+{len(r['funcs_with_bare_except']) - 3})"
        md.append(f"| {r['file_path']} | {funcs} | {r['bare_excepthandlers']} |")
    md.extend([
        "",
        "## Top 10: print 调用最多",
        "",
        "| 文件 | print 次数 |",
        "|---|---:|",
    ])
    rows_print = sorted(rows, key=lambda r: -r["prints"])[:10]
    for r in rows_print:
        if r["prints"] > 0:
            md.append(f"| {r['file_path']} | {r['prints']} |")
    md.extend([
        "",
        "## Top 10: 无 logger 但函数多",
        "",
        "| 文件 | 函数数 |",
        "|---|---:|",
    ])
    rows_no_log = [r for r in rows if not r["module_has_logger"] and r["funcs"] > 3]
    rows_no_log.sort(key=lambda r: -r["funcs"])
    for r in rows_no_log[:10]:
        md.append(f"| {r['file_path']} | {r['funcs']} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    # Stdout.
    print(f"FILES_SCANNED={len(rows)}")
    print(f"TOTAL_FUNCS={total_funcs}")
    print(f"FUNCS_WITH_RETURN_HINT={funcs_with_hint} ({funcs_with_hint * 100 // max(total_funcs, 1)}%)")
    print(f"FUNCS_WITH_LOGGING={funcs_with_log} ({funcs_with_log * 100 // max(total_funcs, 1)}%)")
    print(f"FUNCS_WITH_TRY={funcs_with_try}")
    print(f"EXCEPT_HANDLERS={total_except}")
    print(f"BARE_EXCEPT={bare_except}")
    print(f"FILES_WITH_BARE_EXCEPT={files_with_bare}")
    print(f"FILES_NO_LOGGER={files_no_logger}")
    print(f"FILES_WITH_PRINT={files_with_prints}")
    print(f"TOTAL_PRINTS={total_prints}")
    print("---")
    print("TOP_BARE_FILES:")
    for r in rows_bare[:5]:
        print(f"  [{r['bare_excepthandlers']:2d}] {r['file_path']}")
    print("---")
    print("TOP_PRINT_FILES:")
    for r in rows_print[:5]:
        if r["prints"]:
            print(f"  [{r['prints']:3d}] {r['file_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())