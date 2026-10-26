"""Auto-generate a categorized script capability index (scripts/SCRIPTS_INDEX.md) and provide fast keyword search.

Scans:
  - ``scripts/pipeline/``           : core modular data processing pipeline
  - ``scripts/_tools/``             : repository maintenance, auditing, and skill tooling
  - ``scripts/clinical-automation/``: read-only vendored clinical data automation library
  - ``scripts/_archive/``           : curated reference deliverable templates

Usage:
    python scripts/_tools/generate_scripts_index.py                 # regenerate scripts/SCRIPTS_INDEX.md
    python scripts/_tools/generate_scripts_index.py --search docx   # fast CLI keyword lookup for reuse
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
INDEX_PATH = SCRIPTS_DIR / "SCRIPTS_INDEX.md"


@dataclass
class ScriptEntry:
    rel_path: str
    category: str
    summary: str
    exports: list[str]
    has_cli: bool


def _inspect_py_file(path: Path, category: str) -> ScriptEntry | None:
    if path.name == "__init__.py":
        return None
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return None

    doc = ast.get_docstring(tree) or ""
    first_line = ""
    for line in doc.splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.endswith(".py"):
            first_line = cleaned
            break
    if not first_line and doc:
        first_line = doc.splitlines()[0].strip()

    exports: list[str] = []
    has_cli = False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.append(elt.value)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith("_") and node.name != "main":
                exports.append(node.name)
        elif isinstance(node, ast.If):
            try:
                cond = ast.unparse(node.test)
                if "__name__" in cond and "__main__" in cond:
                    has_cli = True
            except Exception:
                has_cli = False

    rel = path.relative_to(REPO_ROOT).as_posix()
    unique_exports = list(dict.fromkeys(exports))[:6]
    return ScriptEntry(
        rel_path=rel,
        category=category,
        summary=first_line or "Utility script",
        exports=unique_exports,
        has_cli=has_cli,
    )


def collect_entries() -> list[ScriptEntry]:
    entries: list[ScriptEntry] = []

    # 1. Pipeline modules
    pipeline_dir = SCRIPTS_DIR / "pipeline"
    if pipeline_dir.exists():
        for py in sorted(pipeline_dir.rglob("*.py")):
            rel_sub = py.relative_to(pipeline_dir)
            stage = rel_sub.parts[0] if len(rel_sub.parts) > 1 else "core"
            entry = _inspect_py_file(py, f"pipeline/{stage}")
            if entry:
                entries.append(entry)

    # 2. Internal tools
    tools_dir = SCRIPTS_DIR / "_tools"
    if tools_dir.exists():
        for py in sorted(tools_dir.glob("*.py")):
            entry = _inspect_py_file(py, "_tools")
            if entry:
                entries.append(entry)

    # 3. Curated archive templates
    archive_dir = SCRIPTS_DIR / "_archive"
    if archive_dir.exists():
        for py in sorted(archive_dir.glob("*.py")):
            entry = _inspect_py_file(py, "_archive (reference)")
            if entry:
                entries.append(entry)

    return entries


def collect_clinical_automation_modules() -> list[tuple[str, int, str]]:
    """Summarize numbered capability folders in scripts/clinical-automation/."""
    ca_dir = SCRIPTS_DIR / "clinical-automation"
    rows: list[tuple[str, int, str]] = []
    if not ca_dir.exists():
        return rows
    for sub in sorted(ca_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("."):
            continue
        py_files = sorted(sub.rglob("*.py"))
        if not py_files:
            continue
        sample_names = ", ".join(f"`{p.name}`" for p in py_files[:4])
        if len(py_files) > 4:
            sample_names += f" (+{len(py_files) - 4} more)"
        rows.append((f"scripts/clinical-automation/{sub.name}", len(py_files), sample_names))
    return rows


def render_markdown(entries: list[ScriptEntry]) -> str:
    lines: list[str] = [
        "# Global Scripts Capability & Reuse Index (`SCRIPTS_INDEX.md`)",
        "",
        "> **Pre-Flight Reuse Mandate (`AGENTS.md` §4)**: Before writing any new script, search this index or run:",
        "> ```bash",
        "> python scripts/_tools/generate_scripts_index.py --search <keyword>",
        "> ```",
        "> Always import or invoke existing modules in `scripts/pipeline/` or `scripts/_tools/` instead of reinventing the wheel.",
        "",
        "## 1. Core Modular Pipeline (`scripts/pipeline/`)",
        "",
        "| Stage | Script Path | CLI | Public API / Exports | Capability Summary |",
        "|-------|-------------|:---:|----------------------|--------------------|",
    ]

    for e in entries:
        if not e.category.startswith("pipeline/"):
            continue
        cli_badge = "Yes" if e.has_cli else "Lib"
        api_str = ", ".join(f"`{x}`" for x in e.exports) if e.exports else "—"
        summary = e.summary.replace("|", "\\|")
        lines.append(
            f"| `{e.category}` | [`{Path(e.rel_path).name}`]({e.rel_path.replace('scripts/', '')}) | {cli_badge} | {api_str} | {summary} |"
        )

    lines.extend(
        [
            "",
            "## 2. Repository Governance & Automation Tools (`scripts/_tools/`)",
            "",
            "| Script Path | CLI | Public API / Functions | Capability Summary |",
            "|-------------|:---:|------------------------|--------------------|",
        ]
    )

    for e in entries:
        if e.category != "_tools":
            continue
        cli_badge = "Yes" if e.has_cli else "Lib"
        api_str = ", ".join(f"`{x}`" for x in e.exports) if e.exports else "—"
        summary = e.summary.replace("|", "\\|")
        lines.append(
            f"| [`{e.rel_path}`]({e.rel_path.replace('scripts/', '')}) | {cli_badge} | {api_str} | {summary} |"
        )

    ca_rows = collect_clinical_automation_modules()
    if ca_rows:
        lines.extend(
            [
                "",
                "## 3. Vendored Clinical Data Automation Library (`scripts/clinical-automation/` — Read-Only)",
                "",
                "| Module Directory | Script Count | Representative Scripts |",
                "|------------------|:------------:|------------------------|",
            ]
        )
        for mod_path, count, sample_names in ca_rows:
            lines.append(f"| `{mod_path}` | {count} | {sample_names} |")

    archive_entries = [e for e in entries if e.category.startswith("_archive")]
    if archive_entries:
        lines.extend(
            [
                "",
                "## 4. Curated Deliverable Reference Templates (`scripts/_archive/` — Local Reference)",
                "",
                "| Script Name | CLI | Key Functions | Reference Scenario |",
                "|-------------|:---:|---------------|--------------------|",
            ]
        )
        for e in archive_entries:
            cli_badge = "Yes" if e.has_cli else "Lib"
            api_str = ", ".join(f"`{x}`" for x in e.exports) if e.exports else "—"
            summary = e.summary.replace("|", "\\|")
            lines.append(f"| `{Path(e.rel_path).name}` | {cli_badge} | {api_str} | {summary} |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate scripts/SCRIPTS_INDEX.md or search reusable scripts by keyword."
    )
    parser.add_argument(
        "--search",
        "-s",
        default=None,
        help="Search keyword across script paths, exported functions, and summaries",
    )
    args = parser.parse_args()

    entries = collect_entries()
    if args.search:
        kw = args.search.lower()
        hits = [
            e
            for e in entries
            if kw in e.rel_path.lower()
            or kw in e.summary.lower()
            or any(kw in fn.lower() for fn in e.exports)
        ]
        print(f"=== Script Reuse Search: '{args.search}' ({len(hits)} hits) ===")
        for h in hits:
            api = ", ".join(h.exports) if h.exports else "CLI"
            print(f"  [{h.category}] {h.rel_path} ({api})\n    -> {h.summary}")
        return 0

    content = render_markdown(entries)
    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"Generated {INDEX_PATH.relative_to(REPO_ROOT)} with {len(entries)} indexed scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
