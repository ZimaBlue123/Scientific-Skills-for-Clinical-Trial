#!/usr/bin/env python3
"""阶段 1-3 (修正版): 解析 pyflakes 3.4 输出 path:line:col message。"""
from __future__ import annotations
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIST = ROOT / "reports" / "phase1_file_list.txt"
OUT_CAT = ROOT / "reports" / "phase1_pyflakes_categories.md"
OUT_TOP = ROOT / "reports" / "phase1_pyflakes_top_files.md"
PY = sys.executable

LINE_RE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<msg>.+)$")


def main() -> int:
    files = [ROOT / line.strip() for line in LIST.read_text(encoding="utf-8").splitlines() if line.strip()]
    msg_counter: Counter[str] = Counter()
    msg_first_word: Counter[str] = Counter()
    msg_examples: dict[str, str] = {}
    per_file: defaultdict[str, list[tuple[int, str, str]]] = defaultdict(list)
    file_with_issues = 0
    for p in files:
        proc = subprocess.run(
            [PY, "-m", "pyflakes", str(p)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        out = proc.stdout.strip()
        if not out:
            continue
        file_with_issues += 1
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for ln in out.splitlines():
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            line_no = int(m["line"])
            msg = m["msg"].strip()
            msg_counter[msg] += 1
            msg_first_word[msg.split()[0]] += 1
            if msg not in msg_examples:
                msg_examples[msg] = ln.strip()
            per_file[rel].append((line_no, msg, ln.strip()))
    # Category report.
    md = ["# pyflakes 消息分布", "", f"扫描: {len(files)} 文件 / 有问题: {file_with_issues} / 总问题: {sum(msg_counter.values())}", "", "## 按消息首词分组 (粗分类)", "", "| 首词 | 数量 | 含义 |", "|---|---:|---|"]
    word_desc = {
        "'X'": "未使用导入 / 未使用变量",
        "f-string": "f-string 语法问题",
        "redefinition": "重复定义",
        "import": "导入相关",
        "local": "局部变量未使用 / 提前引用",
        "syntax": "语法错误",
        "name": "未定义名 / 重复参数名",
        "comparison": "字面量比较",
        "raise": "raise NotImplemented",
        "break": "break/continue/return 在错误作用域",
        "star": "import *",
        "assertion": "恒真断言",
        "invalid": "非法转义序列",
        "redundant": "冗余括号 / 元组",
    }
    for w, n in sorted(msg_first_word.items(), key=lambda kv: -kv[1])[:20]:
        d = word_desc.get(w, "")
        md.append(f"| `{w}` | {n} | {d} |")
    md.extend(["", "## 完整消息分布 (Top 50)", "", "| 数量 | 消息 |", "|---:|---|"])
    for msg, n in sorted(msg_counter.items(), key=lambda kv: -kv[1])[:50]:
        md.append(f"| {n} | {msg} |")
    OUT_CAT.write_text("\n".join(md) + "\n", encoding="utf-8")
    # Top files.
    md2 = ["# Top 20 有问题的文件", "", "| 文件 | 问题数 | 主要消息 |", "|---|---:|---|"]
    sorted_files = sorted(per_file.items(), key=lambda kv: -len(kv[1]))[:20]
    for rel, issues in sorted_files:
        msgs = Counter(m for _, m, _ in issues)
        primary = ", ".join(f"\"{m}\"×{n}" for m, n in sorted(msgs.items(), key=lambda kv: -kv[1])[:3])
        md2.append(f"| {rel} | {len(issues)} | {primary} |")
    OUT_TOP.write_text("\n".join(md2) + "\n", encoding="utf-8")
    # Stdout.
    print(f"FILES_SCANNED={len(files)}")
    print(f"FILES_WITH_ISSUES={file_with_issues}")
    print(f"TOTAL_ISSUES={sum(msg_counter.values())}")
    print("--- TOP FIRST-WORDS ---")
    for w, n in sorted(msg_first_word.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {w!r:30s} {n}")
    print("--- TOP FILES ---")
    for rel, issues in sorted_files[:15]:
        print(f"  [{len(issues):2d}] {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())