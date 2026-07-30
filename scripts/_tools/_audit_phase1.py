#!/usr/bin/env python3
"""阶段一审计入口：枚举审计范围 + 计数 + 分组。"""
from __future__ import annotations
import pathlib
import sys

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")

def collect() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in ROOT.rglob("*.py"):
        if any(seg.startswith("__pycache__") for seg in p.parts):
            continue
        srel = str(p.relative_to(ROOT)).replace("\\", "/")
        if srel.startswith("scripts/_archive/") or "_archive/" in srel.split("/"):
            continue
        if srel.startswith("scripts/") or srel.startswith("tests/"):
            out.append(p)
        elif srel.startswith("skills/") and "/scripts/" in srel:
            out.append(p)
    return sorted(set(out))


def main() -> int:
    files = collect()
    groups = {
        "scripts_top": 0,
        "scripts_common": 0,
        "scripts_tools": 0,
        "scripts_archive_2026": 0,
        "scripts_selftest": 0,
        "skills": 0,
        "tests": 0,
    }
    for p in files:
        srel = str(p.relative_to(ROOT)).replace("\\", "/")
        if srel.startswith("scripts/_archive_2026_consolidation/"):
            groups["scripts_archive_2026"] += 1
        elif srel.startswith("scripts/common_scripts/"):
            groups["scripts_common"] += 1
        elif srel.startswith("scripts/_tools/"):
            groups["scripts_tools"] += 1
        elif "/_selftest_" in srel:
            groups["scripts_selftest"] += 1
        elif srel.startswith("scripts/"):
            groups["scripts_top"] += 1
        elif srel.startswith("skills/"):
            groups["skills"] += 1
        elif srel.startswith("tests/"):
            groups["tests"] += 1
    total_bytes = sum(p.stat().st_size for p in files)
    print(f"AUDIT_COUNT={len(files)}")
    print(f"AUDIT_BYTES={total_bytes}")
    for k, v in groups.items():
        print(f"  {k:22s}: {v}")
    # Save the file list for later phases.
    out_file = ROOT / "reports" / "phase1_file_list.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        "\n".join(str(p.relative_to(ROOT)).replace("\\", "/") for p in files) + "\n",
        encoding="utf-8",
    )
    print(f"FILE_LIST_WRITTEN={out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())