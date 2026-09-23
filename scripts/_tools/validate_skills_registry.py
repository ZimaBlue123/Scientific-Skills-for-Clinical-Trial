"""Validate the skills registry: frontmatter, internal links, ordering, and duplicates.

Inspired by public-apis/public-apis ``scripts/validate/format.py`` — a strict
registry linter for large-scale Markdown asset catalogues — adapted for the
Agent Skills specification used in this repository.

Complements (does NOT duplicate) the existing ``tests/_contract/structure.py``.
That module returns per-skill problem lists consumed by pytest; this script is a
standalone CLI tool that produces human-readable reports and CI-friendly JSON.

Exit codes:
    0 — all checks pass
    1 — warnings only
    2 — errors found
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

# --------------------------------------------------------------------------- #
# YAML frontmatter helpers (no PyYAML dependency for portability)
# --------------------------------------------------------------------------- #

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)

ALLOWED_FIELDS = frozenset(
    {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
)
VALID_TOOLS = frozenset({"Read", "Write", "Edit", "Bash", "Glob", "Grep"})
MAX_DESCRIPTION_LENGTH = 1024


def _extract_frontmatter(text: str) -> str | None:
    """Return the raw YAML between the opening and closing ``---``."""
    m = _FM_RE.match(text)
    return m.group(1) if m else None


def _top_level_entries(frontmatter: str) -> list[tuple[str, str]]:
    """(key, value) for every unindented ``key: value`` line."""
    entries: list[tuple[str, str]] = []
    for line in frontmatter.splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m:
            entries.append((m.group(1), m.group(2).strip()))
    return entries


def _metadata_scalars(frontmatter: str) -> list[tuple[str, str]]:
    """(key, value) for scalars nested one level under ``metadata:``."""
    lines = frontmatter.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("metadata:"))
    except StopIteration:
        return []
    scalars: list[tuple[str, str]] = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        m = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m and m.group(2).strip():
            scalars.append((m.group(1), m.group(2).strip()))
    return scalars


def _resolve_description(frontmatter: str, value: str) -> str:
    """Resolve multi-line YAML descriptions (folded ``>-`` or literal ``|``)."""
    if value and value not in (">", ">-", "|", "|-"):
        return value.strip("\"'")
    # Multi-line: collect indented continuation lines after `description:`
    lines = frontmatter.splitlines()
    desc_lines: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("description:"):
            collecting = True
            continue
        if collecting:
            if line.startswith((" ", "\t")):
                desc_lines.append(line.strip())
            else:
                break
    return " ".join(desc_lines)


# --------------------------------------------------------------------------- #
# Internal link checker
# --------------------------------------------------------------------------- #

_INLINE_PATH = re.compile(r"`((?:assets|references|scripts)/[A-Za-z0-9_./-]+)`")
_MARKDOWN_LINK = re.compile(r"\]\(((?:assets|references|scripts)/[A-Za-z0-9_./-]+)\)")
_COMMAND_PATH = re.compile(
    r"(?:^|\s)(?:python[23]?|bash|sh|uv run(?: python)?)\s+"
    r"((?:assets|references|scripts)/[A-Za-z0-9_./-]+)"
    r"|(?:^|\s)\./((?:assets|references|scripts)/[A-Za-z0-9_./-]+)"
)


def _check_internal_links(skill_dir: Path, skill_md_text: str) -> list[str]:
    """Check that all referenced ``scripts/``, ``references/``, ``assets/`` paths exist."""
    problems: list[str] = []
    for lineno, line in enumerate(skill_md_text.splitlines(), 1):
        commands = {m for pair in _COMMAND_PATH.findall(line) for m in pair if m}
        refs = set(_INLINE_PATH.findall(line)) | set(_MARKDOWN_LINK.findall(line)) | commands
        for ref in refs:
            if not (skill_dir / ref).exists() and not (REPO_ROOT / ref).exists():
                problems.append(f"L{lineno}: references `{ref}` which does not exist")
    return problems


# --------------------------------------------------------------------------- #
# TF-IDF duplicate detection (adapted from skill_dedupe_report.py)
# --------------------------------------------------------------------------- #

def _tokenize(text: str) -> list[str]:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.lower()
    return re.findall(r"[a-z0-9\u4e00-\u9fff]+", text)


def _find_duplicates(
    skills: list[tuple[str, str]], threshold: float = 0.87
) -> list[tuple[float, str, str]]:
    """Return (similarity, skill_a, skill_b) pairs above threshold."""
    docs: list[tuple[str, Counter]] = []
    for name, text in skills:
        docs.append((name, Counter(_tokenize(text))))

    if len(docs) < 2:
        return []

    # Build IDF
    n = len(docs)
    df: Counter = Counter()
    for _, tf in docs:
        df.update(tf.keys())
    idf = {t: math.log((n + 1) / (v + 1)) + 1.0 for t, v in df.items()}

    # Build TF-IDF vectors
    vecs: list[tuple[str, dict[str, float], float]] = []
    for name, tf in docs:
        w = {t: (1.0 + math.log(v)) * idf.get(t, 0.0) for t, v in tf.items()}
        norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
        vecs.append((name, w, norm))

    hits: list[tuple[float, str, str]] = []
    for i in range(len(vecs)):
        ai, wi, ni = vecs[i]
        for j in range(i + 1, len(vecs)):
            aj, wj, nj = vecs[j]
            # Cosine similarity (iterate smaller dict)
            a, b, an, bn = (wi, wj, ni, nj) if len(wi) <= len(wj) else (wj, wi, nj, ni)
            dot = sum(v * b.get(t, 0.0) for t, v in a.items())
            sim = dot / (an * bn)
            if sim >= threshold:
                hits.append((sim, ai, aj))

    hits.sort(reverse=True)
    return hits


# --------------------------------------------------------------------------- #
# Main validation engine
# --------------------------------------------------------------------------- #

@dataclass
class Issue:
    skill: str
    level: str  # "error" | "warning"
    rule: str
    message: str


@dataclass
class ValidationResult:
    total_skills: int = 0
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_skills": self.total_skills,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [
                {"skill": i.skill, "level": i.level, "rule": i.rule, "message": i.message}
                for i in self.issues
            ],
        }


def validate_registry(
    skills_dir: Path = SKILLS_DIR,
    check_links: bool = True,
    check_duplicates: bool = True,
    dedupe_threshold: float = 0.87,
) -> ValidationResult:
    """Run all registry validation checks and return structured results."""
    result = ValidationResult()
    skill_dirs = sorted(
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    )
    result.total_skills = len(skill_dirs)

    # ── 1. Alphabetical order check ──────────────────────────────────────
    names = [d.name for d in skill_dirs]
    sorted_names = sorted(names, key=str.lower)
    for i, (actual, expected) in enumerate(zip(names, sorted_names)):
        if actual != expected:
            result.issues.append(Issue(
                skill=actual,
                level="warning",
                rule="alphabetical_order",
                message=f"Out of alphabetical order: `{actual}` should be at position "
                        f"of `{expected}` (index {i})",
            ))
            break  # Report only the first out-of-order item

    # ── 2. Per-skill checks ──────────────────────────────────────────────
    texts_for_dedupe: list[tuple[str, str]] = []

    for skill_dir in skill_dirs:
        name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as e:
            result.issues.append(Issue(name, "error", "read_error", str(e)))
            continue

        # Collect text for deduplication
        texts_for_dedupe.append((name, text))

        # ── 2a. Frontmatter existence ────────────────────────────────────
        fm = _extract_frontmatter(text)
        if fm is None:
            result.issues.append(Issue(
                name, "error", "frontmatter_missing",
                "SKILL.md has no `---` delimited YAML frontmatter",
            ))
            continue

        entries = _top_level_entries(fm)
        keys = [k for k, _ in entries]
        values = dict(entries)

        # ── 2b. Required fields ──────────────────────────────────────────
        for req in ("name", "description", "metadata"):
            if req not in keys:
                result.issues.append(Issue(
                    name, "error", f"missing_{req}",
                    f"Frontmatter is missing required field `{req}`",
                ))

        # ── 2c. Unknown fields ───────────────────────────────────────────
        for key in keys:
            if key not in ALLOWED_FIELDS:
                result.issues.append(Issue(
                    name, "error", "unknown_field",
                    f"Top-level `{key}` is not a valid spec field — move under `metadata`",
                ))

        # ── 2d. Name matches directory ───────────────────────────────────
        fm_name = values.get("name", "").strip("\"'")
        if fm_name and fm_name != name:
            result.issues.append(Issue(
                name, "error", "name_mismatch",
                f"Frontmatter name `{fm_name}` does not match directory `{name}`",
            ))

        # ── 2e. Description length ───────────────────────────────────────
        desc_raw = values.get("description", "")
        desc = _resolve_description(fm, desc_raw)
        if desc and len(desc) > MAX_DESCRIPTION_LENGTH:
            result.issues.append(Issue(
                name, "warning", "description_too_long",
                f"Description is {len(desc)} chars, exceeds {MAX_DESCRIPTION_LENGTH}",
            ))

        # ── 2f. allowed-tools format ─────────────────────────────────────
        tools = values.get("allowed-tools")
        if tools is not None:
            if "," in tools or tools.startswith("["):
                result.issues.append(Issue(
                    name, "error", "allowed_tools_format",
                    f"`allowed-tools` must be space-separated, got: {tools}",
                ))
            else:
                for token in tools.split():
                    if token not in VALID_TOOLS:
                        result.issues.append(Issue(
                            name, "warning", "allowed_tools_invalid",
                            f"Unknown tool in `allowed-tools`: `{token}`",
                        ))

        # ── 2g. metadata.version required ────────────────────────────────
        scalars = dict(_metadata_scalars(fm))
        if "metadata" in keys and "version" not in scalars:
            result.issues.append(Issue(
                name, "error", "missing_version",
                "`metadata.version` is required",
            ))

        # ── 2h. Unquoted metadata values ─────────────────────────────────
        for key, value in scalars.items():
            ambiguous = re.fullmatch(
                r"\d+|\d+\.\d+|true|false|yes|no|on|off|\d{4}-\d{2}-\d{2}",
                value, re.I,
            )
            if ambiguous:
                result.issues.append(Issue(
                    name, "warning", "unquoted_metadata",
                    f"`metadata.{key}: {value}` should be quoted to stay a string",
                ))

        # ── 2i. Internal link validity ───────────────────────────────────
        if check_links:
            for problem in _check_internal_links(skill_dir, text):
                result.issues.append(Issue(
                    name, "warning", "broken_link", problem,
                ))

    # ── 3. Duplicate detection ───────────────────────────────────────────
    if check_duplicates and len(texts_for_dedupe) >= 2:
        dupes = _find_duplicates(texts_for_dedupe, threshold=dedupe_threshold)
        for sim, a, b in dupes[:20]:  # Cap at 20 pairs
            result.issues.append(Issue(
                skill=f"{a} <-> {b}",
                level="warning",
                rule="duplicate_content",
                message=f"Cosine similarity {sim:.3f} exceeds threshold {dedupe_threshold}",
            ))

    return result


# --------------------------------------------------------------------------- #
# Output formatters
# --------------------------------------------------------------------------- #

def _format_markdown(result: ValidationResult) -> str:
    lines: list[str] = [
        "# Skills Registry Validation Report\n",
        f"- **Total skills scanned**: {result.total_skills}",
        f"- **Errors**: {result.error_count}",
        f"- **Warnings**: {result.warning_count}\n",
    ]

    if result.error_count == 0 and result.warning_count == 0:
        lines.append("✅ All checks passed.\n")
        return "\n".join(lines)

    # Group by rule
    by_rule: dict[str, list[Issue]] = {}
    for issue in result.issues:
        by_rule.setdefault(issue.rule, []).append(issue)

    for rule, issues in sorted(by_rule.items()):
        errors = [i for i in issues if i.level == "error"]
        warnings = [i for i in issues if i.level == "warning"]
        level_tag = "🔴" if errors else "🟡"
        lines.append(f"## {level_tag} {rule} ({len(issues)} issues)\n")
        for i in issues:
            icon = "❌" if i.level == "error" else "⚠️"
            lines.append(f"- {icon} **{i.skill}**: {i.message}")
        lines.append("")

    return "\n".join(lines)


def _format_json(result: ValidationResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the skills registry for completeness and consistency.",
    )
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help="Write output to file (default: stdout for json, "
             "reports/skills_validation_report.md for markdown)",
    )
    parser.add_argument(
        "--no-links", action="store_true",
        help="Skip internal link validation (faster)",
    )
    parser.add_argument(
        "--no-dedupe", action="store_true",
        help="Skip duplicate content detection (faster)",
    )
    parser.add_argument(
        "--dedupe-threshold", type=float, default=0.87,
        help="Cosine similarity threshold for duplicate detection (default: 0.87)",
    )
    parser.add_argument(
        "--skills-dir", type=str, default=None,
        help="Path to skills directory (default: auto-detect from repo root)",
    )
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir) if args.skills_dir else SKILLS_DIR
    if not skills_dir.is_dir():
        print(f"ERROR: skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(2)

    result = validate_registry(
        skills_dir=skills_dir,
        check_links=not args.no_links,
        check_duplicates=not args.no_dedupe,
        dedupe_threshold=args.dedupe_threshold,
    )

    if args.format == "json":
        output = _format_json(result)
        out_path = args.out
        if out_path:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text(output, encoding="utf-8", newline="\n")
            print(f"Report written to {out_path}", file=sys.stderr)
        else:
            print(output)
    else:
        output = _format_markdown(result)
        out_path = args.out or str(REPO_ROOT / "reports" / "skills_validation_report.md")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(output, encoding="utf-8", newline="\n")
        print(f"Report written to {out_path}", file=sys.stderr)

    if result.error_count > 0:
        sys.exit(2)
    elif result.warning_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
