"""Batch-fix SKILL.md YAML frontmatter to satisfy the structural contract.

Addresses the ~259 contract test failures primarily caused by:
1. Missing ``metadata.version`` field
2. ``name`` not matching the directory name
3. Missing ``metadata`` block entirely

Safety guarantees:
- Only modifies the YAML frontmatter region (between ``---`` delimiters)
- Never touches the Markdown body content below the closing ``---``
- Supports ``--dry-run`` mode for safe preview
- Generates a detailed change report to ``reports/frontmatter_fix_report.md``
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

_FM_RE = re.compile(r"\A(---\n)(.*?)(\n---\n)", re.S)

# Known K-Dense upstream skills have `skill-author: K-Dense Inc.`
# Project-specific skills use a different author or no author at all.


@dataclass
class FixAction:
    skill: str
    field: str
    action: str  # "added" | "corrected"
    old_value: str
    new_value: str


@dataclass
class FixReport:
    total_scanned: int = 0
    total_modified: int = 0
    total_skipped: int = 0
    actions: list[FixAction] = field(default_factory=list)


def _top_level_entries(frontmatter: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in frontmatter.splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m:
            entries.append((m.group(1), m.group(2).strip()))
    return entries


def _metadata_scalars(frontmatter: str) -> dict[str, str]:
    lines = frontmatter.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("metadata:"))
    except StopIteration:
        return {}
    scalars: dict[str, str] = {}
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        m = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m and m.group(2).strip():
            scalars[m.group(1)] = m.group(2).strip().strip("\"'")
    return scalars


def _fix_frontmatter(
    skill_dir: Path,
    dry_run: bool = True,
) -> list[FixAction]:
    """Fix a single skill's frontmatter. Returns list of actions taken."""
    actions: list[FixAction] = []
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        return actions

    text = skill_md.read_text(encoding="utf-8")
    fm_match = _FM_RE.match(text)

    if not fm_match:
        return actions  # No frontmatter to fix

    opening = fm_match.group(1)  # "---\n"
    fm_body = fm_match.group(2)  # The YAML content
    closing = fm_match.group(3)  # "\n---\n"
    rest = text[fm_match.end():]  # Everything after the closing ---

    entries = _top_level_entries(fm_body)
    keys = [k for k, _ in entries]
    values = dict(entries)
    meta = _metadata_scalars(fm_body)
    lines = fm_body.splitlines()
    modified = False

    # ── Fix 1: name mismatch ─────────────────────────────────────────────
    fm_name = values.get("name", "").strip("\"'")
    if "name" in keys and fm_name != skill_name:
        actions.append(FixAction(
            skill=skill_name,
            field="name",
            action="corrected",
            old_value=fm_name,
            new_value=skill_name,
        ))
        # Replace the name line
        for i, line in enumerate(lines):
            if line.startswith("name:"):
                lines[i] = f"name: {skill_name}"
                modified = True
                break

    # ── Fix 2: missing metadata block ────────────────────────────────────
    has_metadata = "metadata" in keys
    if not has_metadata:
        actions.append(FixAction(
            skill=skill_name,
            field="metadata",
            action="added",
            old_value="(missing)",
            new_value='metadata:\n  version: "1.0.0"',
        ))
        lines.append("metadata:")
        lines.append('  version: "1.0.0"')
        modified = True

    # ── Fix 3: missing metadata.version ──────────────────────────────────
    elif "version" not in meta:
        actions.append(FixAction(
            skill=skill_name,
            field="metadata.version",
            action="added",
            old_value="(missing)",
            new_value='"1.0.0"',
        ))
        # Find the metadata: line and insert version right after it
        for i, line in enumerate(lines):
            if line.startswith("metadata:"):
                lines.insert(i + 1, '  version: "1.0.0"')
                modified = True
                break

    # ── Fix 4: unquoted metadata.version (e.g. 1.0 without quotes) ──────
    if "version" in meta:
        raw_version = meta["version"]
        if re.fullmatch(r"\d+\.\d+", raw_version):
            # It's ambiguous (YAML float), needs quoting
            actions.append(FixAction(
                skill=skill_name,
                field="metadata.version",
                action="corrected",
                old_value=raw_version,
                new_value=f'"{raw_version}"',
            ))
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("version:") and line.startswith("  "):
                    lines[i] = f'  version: "{raw_version}"'
                    modified = True
                    break

    # ── Write back if modified ───────────────────────────────────────────
    if modified and not dry_run:
        new_fm = "\n".join(lines)
        new_text = f"{opening}{new_fm}{closing}{rest}"
        skill_md.write_text(new_text, encoding="utf-8", newline="\n")

    return actions


def _generate_report(report: FixReport, dry_run: bool) -> str:
    mode = "DRY RUN (no changes applied)" if dry_run else "APPLIED"
    lines: list[str] = [
        "# Frontmatter Fix Report\n",
        f"**Mode**: {mode}\n",
        f"- **Total skills scanned**: {report.total_scanned}",
        f"- **Skills modified**: {report.total_modified}",
        f"- **Skills skipped (no changes needed)**: {report.total_skipped}",
        f"- **Total fix actions**: {len(report.actions)}\n",
    ]

    if not report.actions:
        lines.append("✅ All skills already conform to the frontmatter spec.\n")
        return "\n".join(lines)

    # Group by action type
    by_field: dict[str, list[FixAction]] = {}
    for a in report.actions:
        by_field.setdefault(a.field, []).append(a)

    for field_name, field_actions in sorted(by_field.items()):
        lines.append(f"## {field_name} ({len(field_actions)} fixes)\n")
        for a in field_actions:
            lines.append(f"- **{a.skill}**: {a.action} `{a.old_value}` → `{a.new_value}`")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-fix SKILL.md YAML frontmatter.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Preview changes without applying them (default)",
    )
    parser.add_argument(
        "--apply", action="store_true", default=False,
        help="Actually apply fixes to SKILL.md files",
    )
    parser.add_argument(
        "--skills-dir", type=str, default=None,
        help="Path to skills directory (default: auto-detect)",
    )
    args = parser.parse_args()

    # Default to dry-run unless --apply is explicitly given
    dry_run = not args.apply

    skills_dir = Path(args.skills_dir) if args.skills_dir else SKILLS_DIR
    if not skills_dir.is_dir():
        print(f"ERROR: skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    report = FixReport()
    skill_dirs = sorted(
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    )
    report.total_scanned = len(skill_dirs)

    for skill_dir in skill_dirs:
        actions = _fix_frontmatter(skill_dir, dry_run=dry_run)
        if actions:
            report.total_modified += 1
            report.actions.extend(actions)
        else:
            report.total_skipped += 1

    # Write report
    report_text = _generate_report(report, dry_run)
    report_path = REPO_ROOT / "reports" / "frontmatter_fix_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    mode_str = "DRY RUN" if dry_run else "APPLIED"
    print(
        f"[{mode_str}] Scanned {report.total_scanned} skills, "
        f"{report.total_modified} need fixes, "
        f"{len(report.actions)} total actions. "
        f"Report: {report_path}",
        file=sys.stderr,
    )

    if dry_run and report.total_modified > 0:
        print("\nRe-run with --apply to actually modify the files.", file=sys.stderr)


if __name__ == "__main__":
    main()
