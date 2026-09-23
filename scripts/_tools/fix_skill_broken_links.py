#!/usr/bin/env python3
"""Repair dangling internal links in ``skills/*/SKILL.md`` documents.

Why this exists
---------------
Directory consolidations move shared tooling out of individual skill folders.
When a ``SKILL.md`` keeps pointing at ``scripts/<tool>.py`` that no longer lives
next to it, the documentation silently rots: agents follow dead paths and the
registry validator reports ``broken_link`` warnings.

This tool rewrites those references to the canonical owner of each script. It is
deliberately *declarative*: every rewrite is an explicit entry in
:data:`REDIRECTS`, so reviewers can audit exactly what is being repointed.

Usage
-----
    python scripts/_tools/fix_skill_broken_links.py [--write]

Without ``--write`` it reports the edits it *would* make (dry run, the default).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"


@dataclass(frozen=True)
class Redirect:
    """A single reference rewrite rule."""

    old: str
    new: str
    reason: str


# Order matters: the first matching rule wins for a given ``(skill, old)`` pair.
REDIRECTS: tuple[Redirect, ...] = (
    Redirect(
        old="scripts/generate_schematic.py",
        new="../scientific-schematics/scripts/generate_schematic.py",
        reason="canonical schematic generator now owned by the scientific-schematics skill",
    ),
    Redirect(
        old="scripts/generate_image.py",
        new="../generate-image/scripts/generate_image.py",
        reason="image generator now owned by the generate-image skill",
    ),
    Redirect(
        old="scripts/pubmed_search_tool.py",
        new="scripts/literature_tools/pubmed_search_tool.py",
        reason="moved into the repo-level literature_tools package",
    ),
    Redirect(
        old="scripts/generate_audit_report_docx.py",
        new="scripts/pipeline/export/docx_builder.py",
        reason="audit-report DOCX assembly now provided by the pipeline export stage",
    ),
)

# Skills that legitimately own their own copy of the referenced script; their
# references are already correct and must never be rewritten.
SELF_OWNED: frozenset[str] = frozenset({"scientific-schematics", "scientific-slides"})


def _resolves(skill_dir: Path, ref: str) -> bool:
    """True when *ref* resolves from the skill directory or the repo root."""
    return (skill_dir / ref).exists() or (REPO_ROOT / ref).exists()


def plan_edits() -> list[tuple[Path, Redirect, int]]:
    """Return ``(skill_md_path, redirect, occurrences)`` for every pending edit."""
    planned: list[tuple[Path, Redirect, int]] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file() or skill_dir.name in SELF_OWNED:
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"  ! skipping {skill_md.name}: not valid UTF-8")
            continue
        for redirect in REDIRECTS:
            if redirect.old not in text:
                continue
            # Skip when the reference already resolves (e.g. the skill has its own copy).
            if _resolves(skill_dir, redirect.old):
                continue
            planned.append((skill_md, redirect, text.count(redirect.old)))
    return planned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply the rewrites (default: dry run)")
    args = parser.parse_args(argv)

    planned = plan_edits()
    if not planned:
        print("No dangling references matched the redirect table.")
        return 0

    total = 0
    for skill_md, redirect, count in planned:
        skill = skill_md.parent.name
        total += count
        print(f"[plan] {skill}: {redirect.old} -> {redirect.new}  ({count}x)")
        print(f"       reason: {redirect.reason}")
        if args.write:
            text = skill_md.read_text(encoding="utf-8")
            skill_md.write_text(text.replace(redirect.old, redirect.new), encoding="utf-8", newline="")

    print(f"\n{'Applied' if args.write else 'Planned'} {len(planned)} rule matches "
          f"covering {total} reference(s).")
    if not args.write:
        print("Dry run only. Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
