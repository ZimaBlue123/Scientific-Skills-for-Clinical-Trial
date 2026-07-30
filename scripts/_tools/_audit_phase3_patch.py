#!/usr/bin/env python3
"""阶段三执行补丁：
1. requirements.txt: 在 xlsx 段之前插入 HTTP/scipy/lxml/defusedxml 4 个新依赖
2. README.md: 在"仓库结构"段落扩充"开发工作流"小节
3. CHANGELOG.md: 在 Unreleased 追加本次重构条目
"""
from __future__ import annotations
import pathlib
import sys

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")

NEW_DEPS = """
# --- HTTP client (used by 27 scripts; NCBI E-utilities etc.) ---
requests>=2.31

# --- Numeric / scientific (used by 6+ scripts; transitive deps made explicit) ---
scipy>=1.10
lxml>=4.9
defusedxml>=0.7   # safe XML parsing for untrusted .docx/.xml input

"""

CHANGELOG_ENTRY = """- **Refactor (scripts/ + docs/)**: 2026-07-30 five-phase project cleanup. Phase 1 audited 240 .py files and fixed a UTF-8 BOM in `scripts/verify_data.py`; phase 2 removed 351 stale `__pycache__/` directories and `.log` artifacts; phase 3 added `requests>=2.31`, `scipy>=1.10`, `lxml>=4.9`, `defusedxml>=0.7` to `requirements.txt` (previously used but undeclared; see `docs/audit_phase1.md` and `reports/phase3_imports.md` for evidence).
- **scripts/ consolidation**: 19 root-level `.py` files migrated into `scripts/`, `scripts/_tools/`, and `scripts/_archive_2026_consolidation/`. See `docs/scripts_consolidation_analysis.md`.
"""

WORKFLOW_BLOCK = """维护约定与更详细解释见 `docs/repo_layout.md`。

---

## 开发工作流

本仓库在每次重大重构时会跑一组**自检脚本**（位于 `scripts/_tools/`）。这些脚本可独立于 IDE / CI 运行，方便人工排查。

```bash
# Phase 1: py_compile + pyflakes 全量扫描
py -3 scripts/_tools/_audit_phase1_compile.py
py -3 scripts/_tools/_audit_phase1_pyflakes.py
py -3 scripts/_tools/_audit_phase1_ast.py

# Phase 2: 扫描冗余文件 / 临时日志（不删除）
py -3 scripts/_tools/_audit_phase2_scan.py
# 拟删除清单写入 docs/cleanup_phase2_plan.md

# Phase 3: 导入依赖审计（与 requirements.txt 对照）
py -3 scripts/_tools/_audit_phase3_imports.py
```

报告分别落在：

- `docs/audit_phase1.md` —— 静态分析 + AST 深度审查
- `docs/cleanup_phase2_plan.md` —— 删除清单（含风险等级）
- `reports/phase3_imports.md` —— 第三方 import 使用矩阵

"""


def patch_requirements() -> bool:
    p = ROOT / "requirements.txt"
    text = p.read_text(encoding="utf-8")
    if "requests>=2.31" in text:
        print("requirements.txt: ALREADY_PATCHED")
        return False
    anchor = "# --- Spreadsheet (xlsx) read/write ---"
    if anchor not in text:
        print("requirements.txt: ANCHOR_NOT_FOUND")
        return False
    new = text.replace(anchor, NEW_DEPS + anchor, 1)
    p.write_text(new, encoding="utf-8")
    print("requirements.txt: PATCHED")
    return True


def patch_readme() -> bool:
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    if "## 开发工作流" in text:
        print("README.md: ALREADY_PATCHED")
        return False
    anchor = "维护约定与更详细解释见 `docs/repo_layout.md`。"
    if anchor not in text:
        print("README.md: ANCHOR_NOT_FOUND")
        return False
    new = text.replace(anchor, anchor + "\n" + WORKFLOW_BLOCK, 1)
    p.write_text(new, encoding="utf-8")
    print("README.md: PATCHED")
    return True


def patch_changelog() -> bool:
    p = ROOT / "CHANGELOG.md"
    text = p.read_text(encoding="utf-8")
    if "five-phase project cleanup" in text:
        print("CHANGELOG.md: ALREADY_PATCHED")
        return False
    anchor = "### Changed\n- **README / README.en**: removed duplicated"
    if anchor not in text:
        print("CHANGELOG.md: ANCHOR_NOT_FOUND")
        return False
    new = text.replace(anchor, "### Changed\n" + CHANGELOG_ENTRY + "- **README / README.en**: removed duplicated", 1)
    p.write_text(new, encoding="utf-8")
    print("CHANGELOG.md: PATCHED")
    return True


def main() -> int:
    r1 = patch_requirements()
    r2 = patch_readme()
    r3 = patch_changelog()
    return 0 if (r1 or r2 or r3) else 1


if __name__ == "__main__":
    sys.exit(main())