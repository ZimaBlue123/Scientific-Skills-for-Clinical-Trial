"""Audit every script in scripts/ for size and inferred purpose.

Produces scripts/_audit_report.md and prints a summary.
"""
from __future__ import annotations
import ast
import re
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts")
SKIP_NAMES = {"__pycache__"}
SKIP_DIRS = {"_archive", "__pycache__"}

CATEGORY_KEYWORDS = {
    "docx_extract":     ["extract_docx", "extract_ib", "extract_tables", "extract_doc_text", "diagnose_docx"],
    "docx_convert":     ["convert_doc_to_docx", "convert_to_md", "convert_audit_report_md_to_docx",
                         "md_to_docx", "make_safe_md_copies", "_extract_docx_text", "extract_docx_to_md"],
    "docx_generate":    ["generate_csr", "generate_audit_report", "generate_clinical", "generate_mmr",
                         "generate_norovirus_review", "generate_phase_summary",
                         "generate_norovirus_trial_lit", "build_tvax006", "cansino_detail",
                         "generate_clinical_overview_doc_review"],
    "xlsx":             ["extract_xlsx_full", "review_clinical_xlsx"],
    "docx_dsur":        ["dsur_transfer", "audit_dsur"],
    "lit_search":       ["pubmed_lit_search", "norovirus_trial_search"],
    "maintenance":      ["cleanup_generated_artifacts", "_selftest_cleanup",
                         "_selftest_ide_history", "register_cleanup_logon_task",
                         "sync_skills_to_global", "on_open_cleanup", "project_self_check",
                         "skill_dedupe_report"],
}


def categorize(name: str) -> str:
    low = name.lower()
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for pat in patterns:
            if pat in low:
                return cat
    return "other"


def docstring_of(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        return ast.get_docstring(tree) or ""
    except Exception:
        return ""


def main():
    rows = []
    for p in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_NAMES:
            continue
        size = p.stat().st_size
        ds = docstring_of(p)
        first_line = ds.split("\n", 1)[0].strip() if ds else "(无docstring)"
        rows.append((str(p.relative_to(ROOT.parent)), size, categorize(p.name), first_line))

    out = ROOT / "_audit_report.md"
    lines = [
        "# scripts/ 审计报告",
        "",
        f"扫描目录: `{ROOT}`",
        f"脚本总数: **{len(rows)}**",
        "",
        "## 按类别汇总",
        "",
        "| 类别 | 数量 |",
        "|---|---:|",
    ]
    by_cat: dict[str, list[tuple]] = {}
    for r in rows:
        by_cat.setdefault(r[2], []).append(r)
    for cat, items in sorted(by_cat.items()):
        lines.append(f"| {cat} | {len(items)} |")

    lines.extend(["", "## 全部脚本详情", "",
                  "| # | 路径 | 大小 (字节) | 类别 | 首行 docstring |",
                  "|---|---|---:|---|---|"])
    for i, (path, size, cat, ds) in enumerate(rows, 1):
        ds_short = ds[:80].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | `{path}` | {size} | {cat} | {ds_short} |")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Total scripts: {len(rows)}")
    for cat, items in sorted(by_cat.items()):
        print(f"  {cat}: {len(items)}")


if __name__ == "__main__":
    main()