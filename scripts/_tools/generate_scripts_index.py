"""Auto-generate a categorized script capability index (scripts/SCRIPTS_INDEX.md) and provide fast keyword search.

Scans:
  - ``scripts/pipeline/``           : core modular data processing pipeline
  - ``scripts/_tools/``             : repository maintenance, auditing, and skill tooling
  - ``scripts/clinical-automation/``: read-only vendored clinical data automation library
  - ``skills/*/scripts/``           : skill-bundled helper scripts (search only + per-skill summary)

For every module the index records the one-line capability summary, the public
API (``__all__`` or public functions/classes), and the CLI arguments discovered
from ``argparse`` ``add_argument`` calls (inputs/outputs).

Usage:
    python scripts/_tools/generate_scripts_index.py                 # regenerate scripts/SCRIPTS_INDEX.md
    python scripts/_tools/generate_scripts_index.py --search docx   # fast CLI keyword lookup for reuse
    python scripts/_tools/generate_scripts_index.py --check         # exit 1 if the index is stale (CI / pre-push)
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_PATH = SCRIPTS_DIR / "SCRIPTS_INDEX.md"

MAX_EXPORTS = 6
MAX_ARGS = 6


@dataclass
class ScriptEntry:
    rel_path: str
    category: str
    summary: str
    exports: list[str]
    has_cli: bool
    cli_args: list[str] = field(default_factory=list)


def _cli_args(tree: ast.AST) -> list[str]:
    """Collect argparse argument names (positional names or long options)."""
    args: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        names = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if not names:
            continue
        longs = [n for n in names if n.startswith("--")]
        args.append(longs[0] if longs else names[0])
    return list(dict.fromkeys(args))


def _inspect_py_file(path: Path, category: str) -> ScriptEntry | None:
    if path.name == "__init__.py":
        return None
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError, OSError) as exc:
        print(f"[warn] skip {path.relative_to(REPO_ROOT).as_posix()}: {exc}", file=sys.stderr)
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
    declared_all: list[str] = []
    has_cli = False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                declared_all.append(elt.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_") and node.name != "main":
                exports.append(node.name)
        elif isinstance(node, ast.If):
            cond = ast.unparse(node.test)
            if "__name__" in cond and "__main__" in cond:
                has_cli = True

    rel = path.relative_to(REPO_ROOT).as_posix()
    chosen = declared_all or exports
    return ScriptEntry(
        rel_path=rel,
        category=category,
        summary=first_line or "Utility script",
        exports=list(dict.fromkeys(chosen))[:MAX_EXPORTS],
        has_cli=has_cli,
        cli_args=_cli_args(tree)[:MAX_ARGS],
    )


def collect_entries(include_vendored: bool = False) -> list[ScriptEntry]:
    entries: list[ScriptEntry] = []

    pipeline_dir = SCRIPTS_DIR / "pipeline"
    if pipeline_dir.exists():
        for py in sorted(pipeline_dir.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            rel_sub = py.relative_to(pipeline_dir)
            stage = rel_sub.parts[0] if len(rel_sub.parts) > 1 else "core"
            entry = _inspect_py_file(py, f"pipeline/{stage}")
            if entry:
                entries.append(entry)

    tools_dir = SCRIPTS_DIR / "_tools"
    if tools_dir.exists():
        for py in sorted(tools_dir.glob("*.py")):
            entry = _inspect_py_file(py, "_tools")
            if entry:
                entries.append(entry)

    if include_vendored:
        ca_dir = SCRIPTS_DIR / "clinical-automation"
        if ca_dir.exists():
            for py in sorted(ca_dir.rglob("*.py")):
                if "__pycache__" in py.parts:
                    continue
                entry = _inspect_py_file(py, "clinical-automation")
                if entry:
                    entries.append(entry)
        if SKILLS_DIR.exists():
            for py in sorted(SKILLS_DIR.glob("*/scripts/**/*.py")):
                if "__pycache__" in py.parts:
                    continue
                skill = py.relative_to(SKILLS_DIR).parts[0]
                entry = _inspect_py_file(py, f"skill:{skill}")
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
        py_files = sorted(p for p in sub.rglob("*.py") if "__pycache__" not in p.parts)
        if not py_files:
            continue
        sample_names = ", ".join(f"`{p.name}`" for p in py_files[:4])
        if len(py_files) > 4:
            sample_names += f" (+{len(py_files) - 4} more)"
        rows.append((f"scripts/clinical-automation/{sub.name}", len(py_files), sample_names))
    return rows


def collect_skill_script_counts() -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    if not SKILLS_DIR.exists():
        return rows
    for skill in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        n = sum(1 for p in (skill / "scripts").rglob("*.py") if "__pycache__" not in p.parts) if (skill / "scripts").is_dir() else 0
        if n:
            rows.append((skill.name, n))
    return rows


def _md(text: str) -> str:
    return text.replace("|", "\\|")


def _fmt_list(items: list[str]) -> str:
    return ", ".join(f"`{x}`" for x in items) if items else "—"


def render_markdown(entries: list[ScriptEntry]) -> str:
    lines: list[str] = [
        "# Global Scripts Capability & Reuse Index (`SCRIPTS_INDEX.md`)",
        "",
        "> **Pre-Flight Reuse Mandate (`AGENTS.md` §4)**: Before writing any new script, search this index",
        "> and [`SKILLS_INDEX.md`](../SKILLS_INDEX.md), or run:",
        "> ```bash",
        "> python scripts/_tools/generate_scripts_index.py --search <keyword>   # also searches clinical-automation + skill scripts",
        "> ```",
        "> Always import or invoke existing modules in `scripts/pipeline/` or `scripts/_tools/` instead of reinventing the wheel.",
        "> This file is auto-generated — edit module docstrings, then re-run `python scripts/_tools/generate_scripts_index.py`.",
        "",
        "Legend: **CLI** = `Yes` (runnable, `__main__` guard) / `Lib` (import only); **CLI Args** = argparse inputs/outputs.",
        "",
        "## 1. Core Modular Pipeline (`scripts/pipeline/`)",
        "",
        "| Stage | Script | CLI | CLI Args | Public API | Capability Summary |",
        "|-------|--------|:---:|----------|------------|--------------------|",
    ]

    for e in entries:
        if not e.category.startswith("pipeline/"):
            continue
        lines.append(
            f"| `{e.category}` | [`{Path(e.rel_path).name}`]({e.rel_path.replace('scripts/', '', 1)}) | "
            f"{'Yes' if e.has_cli else 'Lib'} | {_fmt_list(e.cli_args)} | {_fmt_list(e.exports)} | {_md(e.summary)} |"
        )

    lines.extend(
        [
            "",
            "## 2. Repository Governance & Automation Tools (`scripts/_tools/`)",
            "",
            "| Script | CLI | CLI Args | Capability Summary |",
            "|--------|:---:|----------|--------------------|",
        ]
    )
    for e in entries:
        if e.category != "_tools":
            continue
        lines.append(
            f"| [`{Path(e.rel_path).name}`]({e.rel_path.replace('scripts/', '', 1)}) | "
            f"{'Yes' if e.has_cli else 'Lib'} | {_fmt_list(e.cli_args)} | {_md(e.summary)} |"
        )

    ca_rows = collect_clinical_automation_modules()
    if ca_rows:
        lines.extend(
            [
                "",
                "## 3. Vendored Clinical Data Automation Library (`scripts/clinical-automation/` — Read-Only)",
                "",
                "> Invoke via the `skills/clinical-*` SKILL.md entry points; never edit these scripts directly (`AGENTS.md` §3.1).",
                "",
                "| Module Directory | Script Count | Representative Scripts |",
                "|------------------|:------------:|------------------------|",
            ]
        )
        for mod_path, count, sample_names in ca_rows:
            lines.append(f"| `{mod_path}` | {count} | {sample_names} |")

    skill_rows = collect_skill_script_counts()
    if skill_rows:
        lines.extend(
            [
                "",
                "## 4. Skill-Bundled Scripts (`skills/*/scripts/`)",
                "",
                "> Use through the owning skill's `SKILL.md`. Searchable with `--search`.",
                "",
                "| Skill | Script Count |",
                "|-------|:------------:|",
            ]
        )
        for name, count in skill_rows:
            lines.append(f"| [`{name}`](../skills/{name}/SKILL.md) | {count} |")

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
        help="Search keyword across script paths, exported functions, CLI args and summaries",
    )
    parser.add_argument("--check", action="store_true", help="Exit 1 if SCRIPTS_INDEX.md is out of date")
    args = parser.parse_args()

    if args.search:
        kw = args.search.lower().strip()
        if not kw:
            parser.error("--search keyword must not be empty")
        hits = [
            e
            for e in collect_entries(include_vendored=True)
            if kw in e.rel_path.lower()
            or kw in e.summary.lower()
            or any(kw in fn.lower() for fn in e.exports)
            or any(kw in a.lower() for a in e.cli_args)
        ]
        print(f"=== Script Reuse Search: '{args.search}' ({len(hits)} hits) ===")
        for h in hits:
            api = ", ".join(h.exports) if h.exports else "CLI"
            cli = f"  args: {' '.join(h.cli_args)}" if h.cli_args else ""
            print(f"  [{h.category}] {h.rel_path} ({api}){cli}\n    -> {h.summary}")
        return 0

    content = render_markdown(collect_entries())
    if args.check:
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        if current.replace("\r\n", "\n") != content:
            print(f"{INDEX_PATH.relative_to(REPO_ROOT).as_posix()} is stale; run generate_scripts_index.py", file=sys.stderr)
            return 1
        print("SCRIPTS_INDEX.md is up to date.")
        return 0

    INDEX_PATH.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {INDEX_PATH.relative_to(REPO_ROOT).as_posix()} with {len(collect_entries())} indexed scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
