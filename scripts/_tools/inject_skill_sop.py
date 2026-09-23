#!/usr/bin/env python3
"""Inject the standard Pre-flight / Post-execution SOP into core skills.

Scope
-----
Only the *core* skills of this repository receive the SOP — those listed under the
"临床试验 & 合规" (Clinical Trials & Compliance) section of ``SKILLS_INDEX.md``,
which is the domain this project exists to serve. Injecting it into all 175 skills
would produce enormous, low-value churn in third-party scientific library wrappers.

The wording is intentionally identical to the canonical block already present in
``skills/pptx-gmc-sync-from-word/SKILL.md`` so the repository stays consistent.

Usage
-----
    python scripts/_tools/inject_skill_sop.py [--write]

Without ``--write`` it reports which skills would change (dry run, the default).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_PATH = REPO_ROOT / "SKILLS_INDEX.md"

# Section in SKILLS_INDEX.md that defines the project's core skill set.
CORE_SECTION_PREFIX = "临床试验 & 合规"

_PREFLIGHT_HEADING = "## Pre-flight Check"
_POST_HEADING = "## Post-execution Validation"

SOP_BLOCK = f"""
{_PREFLIGHT_HEADING}

Before executing, the agent MUST:
1. Verify input file exists at the expected path
2. Clear any cached results from previous runs
3. Confirm required environment variables are set

{_POST_HEADING}

After execution, the agent MUST:
1. Verify output file was created successfully
2. Run applicable validator (if available)
3. Report results in standardized Markdown table format
"""

# Index rows look like: ``| [skill-name](skills/skill-name/SKILL.md) | description | ...``
_SKILL_LINK_RE = re.compile(r"^\[([^\]]+)\]\(skills/")


def read_core_skill_names() -> list[str]:
    """Return the skill names listed under the core section of the index."""
    lines = INDEX_PATH.read_text(encoding="utf-8").splitlines()
    names: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            inside = CORE_SECTION_PREFIX in line
            continue
        if inside:
            # Table rows are prefixed with a pipe; normalise before matching.
            cell = line.strip().lstrip("|").strip()
            m = _SKILL_LINK_RE.match(cell)
            if m:
                names.append(m.group(1))
    return sorted(set(names))


def needs_injection(text: str) -> bool:
    return _PREFLIGHT_HEADING not in text and _POST_HEADING not in text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Append the SOP block (default: dry run)")
    args = parser.parse_args(argv)

    core = read_core_skill_names()
    if not core:
        print(f"! no skills parsed from the '{CORE_SECTION_PREFIX}' section of {INDEX_PATH.name}")
        return 1

    pending: list[str] = []
    skipped: list[str] = []
    for name in core:
        skill_md = SKILLS_DIR / name / "SKILL.md"
        if not skill_md.is_file():
            print(f"  ! core skill '{name}' has no SKILL.md; skipped")
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"  ! core skill '{name}' is not valid UTF-8; skipped")
            continue
        if not needs_injection(text):
            skipped.append(name)
            continue
        pending.append(name)
        if args.write:
            new_text = text.rstrip("\n") + "\n" + SOP_BLOCK
            skill_md.write_text(new_text, encoding="utf-8", newline="")

    print(f"Core skills detected: {len(core)}")
    print(f"Already have SOP: {len(skipped)} -> {skipped}")
    print(f"{'Updated' if args.write else 'Would update'}: {len(pending)} -> {pending}")
    if pending and not args.write:
        print("Dry run only. Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
