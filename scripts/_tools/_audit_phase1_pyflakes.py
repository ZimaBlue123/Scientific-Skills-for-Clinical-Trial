#!/usr/bin/env python3
"""阶段 1-3: pyflakes 全量扫描。结果分类写入 reports/。"""
from __future__ import annotations
import pathlib
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIST = ROOT / "reports" / "phase1_file_list.txt"
OUT_RAW = ROOT / "reports" / "phase1_pyflakes_raw.txt"
OUT_BY = ROOT / "reports" / "phase1_pyflakes_by_file.txt"
OUT_SUM = ROOT / "reports" / "phase1_pyflakes_summary.md"
PY = sys.executable

CATEGORIES = {
    "F401": "imported but unused",
    "F402": "imported as both name and alias",
    "F403": "from X import * used",
    "F404": "__future__ import not first",
    "F405": "star may be undefined",
    "F406": "star in __all__",
    "F407": "future import not allowed",
    "F501": "invalid escape sequence",
    "F502": "% formatting in f-string",
    "F503": "triple-quote string reuse",
    "F504": "percent with dict",
    "F505": "missing whitespace",
    "F506": "not enough quotes",
    "F601": "multi-value repeated key",
    "F602": "key repeated",
    "F621": "redundant parentheses",
    "F622": "redundant tuple in comprehension",
    "F631": "assertion always true",
    "F632": "use == to compare literals",
    "F633": "use of >> with int literal",
    "F634": "multiple assignments on one line",
    "F701": "break outside loop",
    "F702": "continue outside loop",
    "F703": "return outside function",
    "F704": "yield outside function",
    "F705": "return in generator",
    "F706": "return from finally",
    "F707": "break in finally",
    "F722": "syntax error in annotation",
    "F811": "redefinition of unused name",
    "F812": "redefinition of unused name",
    "F821": "undefined name",
    "F822": "undefined name in __all__",
    "F823": "local variable referenced before assignment",
    "F831": "duplicate argument name",
    "F841": "local variable assigned but never used",
    "F901": "raise NotImplemented",
}


def main() -> int:
    files = [ROOT / line.strip() for line in LIST.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw_lines: list[str] = []
    by_file: dict[str, list[str]] = defaultdict(list)
    cat_counter: dict[str, int] = defaultdict(int)
    file_with_issues = 0
    for p in files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        proc = subprocess.run(
            [PY, "-m", "pyflakes", str(p)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        out = proc.stdout.strip()
        if not out:
            continue
        file_with_issues += 1
        raw_lines.append(f"=== {rel} ===")
        raw_lines.append(out)
        raw_lines.append("")
        for ln in out.splitlines():
            by_file[rel].append(ln.strip())
            # Extract category code.
            code = ln.split(":")[2].strip().split()[0] if ln.count(":") >= 2 else "UNKNOWN"
            cat_counter[code] += 1
    OUT_RAW.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    # Per-file listing.
    by_lines = [f"{rel} ({len(lines)} issues)" for rel, lines in sorted(by_file.items())]
    OUT_BY.write_text("\n".join(by_lines) + "\n", encoding="utf-8")
    # Summary.
    summary = ["# Phase 1-3 pyflakes 汇总", "", f"扫描文件: {len(files)}", f"有问题的文件: {file_with_issues}", "", "## 类别分布", "", "| 类别 | 描述 | 数量 |", "|---|---|---:|"]
    for code, n in sorted(cat_counter.items(), key=lambda kv: -kv[1]):
        desc = CATEGORIES.get(code, "?")
        summary.append(f"| {code} | {desc} | {n} |")
    summary.extend(["", "## 有问题的文件 (按问题数排序)", "", "| 文件 | 问题数 |", "|---|---:|"])
    for rel, n in sorted(((r, len(l)) for r, l in by_file.items()), key=lambda kv: -kv[1]):
        summary.append(f"| {rel} | {n} |")
    OUT_SUM.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"FILES_SCANNED={len(files)}")
    print(f"FILES_WITH_ISSUES={file_with_issues}")
    print(f"TOTAL_ISSUES={sum(cat_counter.values())}")
    print(f"TOP_CATEGORIES=" + ", ".join(f"{c}:{n}" for c, n in sorted(cat_counter.items(), key=lambda kv: -kv[1])[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())