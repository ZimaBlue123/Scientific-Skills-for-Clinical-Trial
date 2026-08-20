#!/usr/bin/env python3
"""阶段 1-3: 从已有的 phase1_pyflakes_raw.txt 解析（不重跑 pyflakes）。"""
from __future__ import annotations

import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
RAW = ROOT / "reports" / "phase1_pyflakes_raw.txt"
OUT_CAT = ROOT / "reports" / "phase1_pyflakes_categories.md"
OUT_TOP = ROOT / "reports" / "phase1_pyflakes_top_files.md"

# Windows 路径可含 : 盘符，故用更宽容的正则。
LINE_RE = re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+):\s+(?P<msg>.+)$")


def main() -> int:
    msg_counter: Counter[str] = Counter()
    msg_first_word: Counter[str] = Counter()
    msg_examples: dict[str, str] = {}
    per_file: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)
    file_count = 0
    current = None
    for ln in RAW.read_text(encoding="utf-8").splitlines():
        if ln.startswith("=== ") and ln.endswith(" ==="):
            current = ln[4:-4]
            file_count += 1
            continue
        m = LINE_RE.match(ln)
        if not m:
            continue
        if current is None:
            continue
        msg = m["msg"].strip()
        msg_counter[msg] += 1
        msg_first_word[msg.split()[0]] += 1
        if msg not in msg_examples:
            msg_examples[msg] = ln
        per_file[current].append((int(m["line"]), msg))
    # Category report.
    word_desc = {
        "'X'": "未使用导入 / 未使用变量 (imported/assigned but unused)",
        "f-string": "f-string 语法问题 (missing placeholders)",
        "redefinition": "重复定义 (redefinition)",
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
        "duplicate": "重复键",
        "may": "from X import * (可能未定义)",
        "shadowing": "导入星号 shadowing builtin",
    }
    md = [
        "# pyflakes 消息分布",
        "",
        f"扫描: {file_count} 文件 / 有问题: {len(per_file)} / 总问题: {sum(msg_counter.values())}",
        "",
        "## 按消息首词分组 (粗分类)",
        "",
        "| 首词 | 数量 | 含义 |",
        "|---|---:|---|",
    ]
    for w, n in sorted(msg_first_word.items(), key=lambda kv: -kv[1]):
        d = word_desc.get(w, "")
        md.append(f"| `{w}` | {n} | {d} |")
    md.extend([
        "",
        "## 完整消息分布 (Top 50)",
        "",
        "| 数量 | 消息 |",
        "|---:|---|",
    ])
    for msg, n in sorted(msg_counter.items(), key=lambda kv: -kv[1])[:50]:
        md.append(f"| {n} | {msg.replace('|', chr(92)+'|')} |")
    OUT_CAT.write_text("\n".join(md) + "\n", encoding="utf-8")
    # Top files.
    md2 = ["# Top 20 有问题的文件", "", "| 文件 | 问题数 | 主要消息 |", "|---|---:|---|"]
    sorted_files = sorted(per_file.items(), key=lambda kv: -len(kv[1]))[:20]
    for rel, issues in sorted_files:
        msgs = Counter(m for _, m in issues)
        primary = ", ".join(f"\"{m[:40]}\"×{n}" for m, n in sorted(msgs.items(), key=lambda kv: -kv[1])[:3])
        md2.append(f"| {rel} | {len(issues)} | {primary} |")
    OUT_TOP.write_text("\n".join(md2) + "\n", encoding="utf-8")
    # Stdout summary.
    print(f"FILES_WITH_ISSUES={len(per_file)}")
    print(f"TOTAL_ISSUES={sum(msg_counter.values())}")
    print("--- TOP FIRST-WORDS ---")
    for w, n in sorted(msg_first_word.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {w!r:30s} {n}")
    print("--- TOP MESSAGES ---")
    for msg, n in sorted(msg_counter.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  [{n:3d}] {msg[:70]}")
    print("--- TOP FILES ---")
    for rel, issues in sorted_files[:15]:
        print(f"  [{len(issues):2d}] {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())