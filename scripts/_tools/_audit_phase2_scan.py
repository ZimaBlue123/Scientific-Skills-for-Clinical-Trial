#!/usr/bin/env python3
"""阶段二：冗余文件扫描。

仅扫描，绝不删除。输出：
- reports/phase2_scan.json  (机器可读)
- docs/cleanup_phase2_plan.md (人类可读，含分类 + 拟删除清单)

模式：
- AUTO_CLEAR  : 系统产物（__pycache__ / .DS_Store / .pyc / *.bak）→ 高置信度拟删除
- LIKELY_TMP  : 临时日志（*.log / *.tmp / *.err 等）→ 中置信度
- UNTRACKED   : 业务输出文本（review_report.md / verify_data_result.txt 等）→ 低置信度，需人工判断
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")

# 永远不扫描的位置（系统 / 已追踪目录）。
SKIP_DIRS = {".git", "node_modules"}
SKIP_FILES = {".gitignore", ".gitattributes", ".editorconfig"}

# 模式 → 分类
AUTO_CLEAR_PATTERNS = [
    ("__pycache__", "directory", "Python bytecode cache"),
    (".DS_Store", "file", "macOS directory metadata"),
    ("Thumbs.db", "file", "Windows thumbnail cache"),
    ("*.pyc", "file", "Python compiled bytecode"),
    ("*.pyo", "file", "Python optimized bytecode"),
    ("*.pyd", "file", "Python C extension"),
    ("*.bak", "file", "manual backup"),
    ("*.swp", "file", "vim swap file"),
    ("*.swo", "file", "vim swap file"),
    ("*~", "file", "editor backup"),
]
LIKELY_TMP_PATTERNS = [
    (r"\.log$", "file", "runtime log"),
    (r"\.tmp$", "file", "temporary file"),
    (r"\.pid$", "file", "PID lock file"),
    (r"\.orig$", "file", "merge original"),
    (r"\.rej$", "file", "merge reject"),
    (r"\.err$", "file", "stderr capture"),
]
# 业务保留（已识别为有意义的产物）
PROTECT_FILES = {
    "review_report.md",  # 业务报告
    "verify_data_result.txt",  # verify_data.py 输出
    "cleanup_plan.md",  # scan_cleanup.py 生成的清理计划
    "docs/audit_phase1.md",  # 阶段一报告
    "scripts_consolidation_analysis.md",  # 上一轮报告
}
# 阶段二保护
PHASE2_PROTECT = {
    "docs/cleanup_phase2_plan.md",  # 阶段二计划（自身）
    "reports/phase2_scan.json",  # 阶段二扫描结果
}


@dataclass
class Hit:
    path: str
    size: int
    mtime: float
    kind: str  # directory / file
    pattern: str
    reason: str
    confidence: str  # HIGH / MEDIUM / LOW
    bucket: str  # AUTO_CLEAR / LIKELY_TMP / UNTRACKED
    protect_reason: str = ""


def _matches(name: str, pat: str) -> bool:
    """Glob-style match (no fnmatch fnmatching for **)."""
    import fnmatch
    return fnmatch.fnmatch(name, pat)


def _is_in_protected(rel: pathlib.Path) -> str | None:
    s = str(rel).replace("\\", "/")
    for p in PROTECT_FILES | PHASE2_PROTECT:
        if s == p or s.endswith("/" + p):
            return p
    return None


def _classify(rel: pathlib.Path, full: pathlib.Path) -> Hit | None:
    """Classify a single path. Return None if should be skipped."""
    name = full.name
    # Directories.
    if full.is_dir():
        for pat, _kind, reason in AUTO_CLEAR_PATTERNS:
            if pat == name or _matches(name, pat):
                return Hit(
                    path=str(rel).replace("\\", "/"),
                    size=sum(p.stat().st_size for p in full.rglob("*") if p.is_file()),
                    mtime=full.stat().st_mtime,
                    kind="directory",
                    pattern=pat,
                    reason=reason,
                    confidence="HIGH",
                    bucket="AUTO_CLEAR",
                )
        return None
    # Files.
    for pat, _kind, reason in AUTO_CLEAR_PATTERNS:
        if _matches(name, pat):
            return Hit(
                path=str(rel).replace("\\", "/"),
                size=full.stat().st_size,
                mtime=full.stat().st_mtime,
                kind="file",
                pattern=pat,
                reason=reason,
                confidence="HIGH",
                bucket="AUTO_CLEAR",
            )
    for pat, _kind, reason in LIKELY_TMP_PATTERNS:
        if re.search(pat, name):
            return Hit(
                path=str(rel).replace("\\", "/"),
                size=full.stat().st_size,
                mtime=full.stat().st_mtime,
                kind="file",
                pattern=pat,
                reason=reason,
                confidence="MEDIUM",
                bucket="LIKELY_TMP",
            )
    return None


def scan() -> list[Hit]:
    hits: list[Hit] = []
    for p in sorted(ROOT.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        rel = p.relative_to(ROOT)
        if _is_in_protected(rel):
            continue
        h = _classify(rel, p)
        if h is not None:
            hits.append(h)
    return hits


def collect_untracked() -> list[Hit]:
    """List files git considers untracked; classify as LOW-confidence UNTRACKED."""
    import subprocess
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    out = []
    for line in proc.stdout.splitlines():
        if not line.startswith("?? "):
            continue
        path_str = line[3:].strip().strip('"')
        full = ROOT / path_str
        if not full.exists() or full.is_dir():
            continue
        rel = full.relative_to(ROOT)
        if _is_in_protected(rel):
            continue
        # Skip if already classified by scan().
        out.append(Hit(
            path=str(rel).replace("\\", "/"),
            size=full.stat().st_size,
            mtime=full.stat().st_mtime,
            kind="file",
            pattern="(untracked)",
            reason="git untracked file (NOT in .gitignore); business deliverable or temp output",
            confidence="LOW",
            bucket="UNTRACKED",
        ))
    return out


def main() -> int:
    auto_clear = scan()
    untracked = collect_untracked()
    all_hits = auto_clear + untracked
    all_hits.sort(key=lambda h: (h.bucket, h.path))

    # JSON output.
    json_path = ROOT / "reports" / "phase2_scan.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps([asdict(h) for h in all_hits], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Markdown output.
    md_path = ROOT / "docs" / "cleanup_phase2_plan.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[Hit]] = defaultdict(list)
    for h in all_hits:
        grouped[h.bucket].append(h)
    lines = [
        "# 阶段二清理计划 (Phase 2 Cleanup Plan)",
        "",
        "> **本文件为扫描结果草案，未执行任何删除。**",
        "> 执行需用户明确批准。基线 commit: `0e5207a`（可回滚）。",
        "",
        "## 扫描摘要",
        "",
        f"- **HIGH 置信度（AUTO_CLEAR）**: {len(grouped['AUTO_CLEAR'])} 项（系统缓存 / 临时副本）",
        f"- **MEDIUM 置信度（LIKELY_TMP）**: {len(grouped['LIKELY_TMP'])} 项（*.log / *.tmp 等）",
        f"- **LOW 置信度（UNTRACKED）**: {len(grouped['UNTRACKED'])} 项（git 未追踪，需人工判断）",
        "",
        f"**总计**: {len(all_hits)} 项 / {sum(h.size for h in all_hits):,} bytes",
        "",
    ]
    titles = {
        "AUTO_CLEAR": ("🟢 高置信度（AUTO_CLEAR）", "系统产物：可安全删除"),
        "LIKELY_TMP": ("🟡 中置信度（LIKELY_TMP）", "临时日志：通常可删除，建议抽查"),
        "UNTRACKED": ("🔴 低置信度（UNTRACKED）", "git 未追踪：业务产物或临时输出，需人工判定"),
    }
    for bucket in ("AUTO_CLEAR", "LIKELY_TMP", "UNTRACKED"):
        hits = grouped[bucket]
        if not hits:
            continue
        title, desc = titles[bucket]
        lines.append(f"## {title}")
        lines.append("")
        lines.append(desc)
        lines.append("")
        lines.append("| # | 路径 | 大小 (B) | 模式 | 理由 |")
        lines.append("|---:|---|---:|---|---|")
        for i, h in enumerate(hits, 1):
            lines.append(f"| {i} | `{h.path}` | {h.size:,} | `{h.pattern}` | {h.reason} |")
        lines.append("")
    lines.extend([
        "## 受保护文件（不会处理）",
        "",
        "```",
        *[f"  {p}" for p in sorted(PROTECT_FILES | PHASE2_PROTECT)],
        "```",
        "",
        "## 待用户指令",
        "",
        "- 全部批准：回复「**批准删除**」将执行 HIGH + MEDIUM 全部；LOW 跳过",
        "- 仅 HIGH：回复「**仅高置信度**」",
        "- 列出子集：回复「**仅删除 X, Y, Z**」",
        "- 全部拒绝：回复「**取消**」",
        "",
        "## 回滚预案",
        "",
        "- 当前基线 commit: `0e5207a`",
        "- 回滚命令: `git reset --hard 0e5207a`（会丢弃所有 untracked 工作）",
        "- 软回滚（保留工作）: `git reset --soft 0e5207a`",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"SCAN_DIRS={len(grouped['AUTO_CLEAR'])}")
    print(f"LIKELY_TMP={len(grouped['LIKELY_TMP'])}")
    print(f"UNTRACKED={len(grouped['UNTRACKED'])}")
    print(f"TOTAL_BYTES={sum(h.size for h in all_hits):,}")
    print(f"JSON={json_path}")
    print(f"MD={md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())