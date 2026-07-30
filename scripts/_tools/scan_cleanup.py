#!/usr/bin/env python3
"""Phase 2 — scan workspace for redundant/untracked files (FAST version).

Uses ``git status --porcelain`` to enumerate untracked + modified entries
in one pass (much faster than ``git ls-files --error-unmatch`` per path).

Outputs ``cleanup_plan.md`` — a candidate-deletion manifest for user
approval. NO file is removed by this script.
"""
from __future__ import annotations

import fnmatch
import logging
import re
import subprocess
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("scan_cleanup")

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")

# Audit deliverables: keep regardless of heuristic.
PROTECT = {
    "extracted_review_doc.txt",
    "verify_data_result.txt",
    "review_report.md",
    "output_doc_full.txt",
    "cross_check_result.txt",
}

# Patterns that mark a file as redundant/ephemeral.
DELETE_PATTERNS = (
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.log",
    "*.tmp",
    "*.bak",
    "*~",
    "pip_install*.log",
    "probe*.log",
    "dir.log",
    "ls.log",
    "ex.log",
    "vd.log",
    "as.log",
    "commit1.log",
    "extract_help.txt",
    "filelist.txt",
)


def matches_pattern(name: str) -> bool:
    for pat in DELETE_PATTERNS:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def get_untracked(root: Path) -> list[str]:
    """Return untracked file paths via `git status --porcelain` (fast)."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.error("git status failed: %s", result.stderr.strip())
        return []
    # Format: "XY <path>" where XY is 2 chars + space. Untracked = "??".
    out: list[str] = []
    for line in result.stdout.splitlines():
        m = re.match(r"^\?\? (.*)$", line)
        if m:
            out.append(m.group(1).strip().strip('"'))
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    untracked = get_untracked(ROOT)
    logger.info("git reports %d untracked entries", len(untracked))

    candidates: list[tuple[str, int, str]] = []
    for rel in untracked:
        p = (ROOT / rel).resolve()
        try:
            # git may quote paths with spaces; strip quotes
            rel_clean = rel.strip('"')
            p = (ROOT / rel_clean).resolve()
        except OSError as exc:
            logger.warning("skipping %s: %s", rel, exc)
            continue

        if p.is_dir():
            # Untracked empty directories → not handled here
            continue

        name = p.name
        if name in PROTECT:
            logger.info("PROTECT %s", rel_clean)
            continue

        reason: str | None = None
        if any(part == "__pycache__" for part in p.parts):
            reason = "Python bytecode cache directory"
        elif matches_pattern(name):
            reason = "matches redundant pattern"
        elif name == "extract_review_doc.py":
            reason = "obsolete prototype (replaced by extract_review_doc_stdlib.py)"

        if reason is None:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            size = -1
        candidates.append((rel_clean, size, reason))

    plan = ROOT / "cleanup_plan.md"
    lines = [
        "# Phase 2 — 拟删除文件清单（待批准）",
        "",
        f"- 根目录: `{ROOT}`",
        f"- 扫描规则: 未追踪文件 + 匹配启发式 pattern 或已废弃原型",
        f"- 扫描结果: **{len(candidates)} 个候选文件**",
        "",
        "| # | 路径 | 大小 (字节) | 判定理由 |",
        "|---|---|---:|---|",
    ]
    for i, (rel, size, reason) in enumerate(candidates, 1):
        lines.append(f"| {i} | `{rel}` | {size} | {reason} |")

    lines.extend([
        "",
        "## 受保护文件（**不删除**）",
        "",
        "以下文件虽未被 Git 追踪，但属于本次审查的可交付成果，**保留**：",
        "",
        "- `extracted_review_doc.txt` — 文本提取产物",
        "- `verify_data_result.txt` — 算术校验产物",
        "- `review_report.md` — 主审查报告",
        "- `output_doc_full.txt` — 预先存在的审计产物",
        "- `cross_check_result.txt` — 预先存在的审计产物",
        "",
        "## 操作说明",
        "",
        "请回复 **\"批准删除\"** 或明确批准的项目编号，才会真正删除上述文件。",
        "若发生误操作，可通过阶段一本地提交 `f26f859` 回滚：",
        "```",
        "git reset --hard f26f859",
        "```",
        "",
    ])
    plan.write_text("\n".join(lines), encoding="utf-8")
    logger.info("plan written to %s (%d candidates)", plan, len(candidates))
    return 0


if __name__ == "__main__":
    sys.exit(main())