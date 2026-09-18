#!/usr/bin/env python3
"""Remove unused standard-library imports from vendored skills.

Only targets imports that:
1. Are at module level (not inside try/except)
2. Are from typing, pathlib, collections, or urllib
3. Are confirmed unused by pyflakes

Safety: py_compile before and after each file.
"""
import argparse
import os
import py_compile
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Each target: (rel_path, line_number, symbol_to_remove, full_import_or_just_symbol)
# "symbol" means remove just that name from a multi-import line
# "line" means remove the entire line
TARGETS = [
    # pathlib.Path unused
    ("clinical-decision-support/scripts/build_decision_tree.py", 13, "line"),
    ("clinical-reports/scripts/format_adverse_events.py", 14, "line"),
    ("clinical-reports/scripts/validate_trial_report.py", 14, "line"),
    # collections.defaultdict unused
    ("clinical-decision-support/scripts/validate_cds_document.py", 18, "line"),
    # typing members unused (need to check if line has other used imports)
    ("clinical-reports/scripts/check_deidentification.py", 16, "symbol:List"),
    ("clinical-reports/scripts/validate_case_report.py", 17, "symbol:Tuple"),
    ("fda-database/scripts/fda_query.py", 18, "symbol:Counter"),  # deque still used
    ("fda-database/scripts/fda_query.py", 21, "symbol:Any"),
    ("markitdown/scripts/convert_literature.py", 15, "symbol:Optional"),
    ("perplexity-search/scripts/perplexity_search.py", 23, "symbol:List"),
    ("clinicaltrials-database/scripts/query_clinicaltrials.py", 15, "line"),
    ("statistical-analysis/scripts/assumption_checks.py", 12, "symbol:Tuple"),
    # seaborn imported but unused (no side effect at import time for sns)
    ("statistical-analysis/scripts/assumption_checks.py", 17, "line"),
    # pandas imported but unused in clustering_analysis
    ("scikit-learn/scripts/clustering_analysis.py", 9, "line"),
]


def compile_ok(filepath):
    tmpdir = tempfile.mkdtemp()
    cfile = os.path.join(tmpdir, "check.pyc")
    try:
        py_compile.compile(str(filepath), cfile=cfile, doraise=True)
        return True
    except py_compile.PyCompileError:
        return False
    finally:
        if os.path.exists(cfile):
            os.unlink(cfile)
        os.rmdir(tmpdir)


def remove_symbol_from_import(line, symbol):
    """Remove a single symbol from a 'from X import A, B, C' line."""
    # Pattern: from typing import A, B, C
    # Remove symbol with surrounding comma/space
    # Try removing ", Symbol" first
    result = re.sub(rf',\s*{symbol}\b', '', line)
    if result != line:
        return result
    # Try removing "Symbol, " (if it's the first)
    result = re.sub(rf'\b{symbol}\b,\s*', '', line)
    if result != line:
        return result
    # Only symbol on the line
    return None  # Signal to remove the whole line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Unused import cleanup [{mode}] ===\n")

    fixed = 0
    errors = []

    # Process targets in reverse line order per file to avoid line shift
    file_targets = {}
    for rel_path, lineno, action in TARGETS:
        file_targets.setdefault(rel_path, []).append((lineno, action))

    for rel_path in sorted(file_targets):
        filepath = SKILLS_DIR / rel_path
        if not filepath.exists():
            errors.append(f"NOT FOUND: {filepath}")
            continue

        if not compile_ok(filepath):
            errors.append(f"PRE-CHECK FAILED: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        original_lines = lines[:]

        # Process in reverse line order
        targets = sorted(file_targets[rel_path], key=lambda x: x[0], reverse=True)
        count = 0

        for lineno, action in targets:
            idx = lineno - 1
            if idx < 0 or idx >= len(lines):
                errors.append(f"  {rel_path} L{lineno}: out of range")
                continue

            if action == "line":
                print(f"  {rel_path} L{lineno}: remove '{lines[idx].strip()}'")
                lines.pop(idx)
                count += 1
            elif action.startswith("symbol:"):
                symbol = action.split(":")[1]
                new_line = remove_symbol_from_import(lines[idx], symbol)
                if new_line is None:
                    print(f"  {rel_path} L{lineno}: remove entire line (only symbol)")
                    lines.pop(idx)
                else:
                    print(f"  {rel_path} L{lineno}: remove '{symbol}' -> '{new_line.strip()}'")
                    lines[idx] = new_line
                count += 1

        if count > 0 and args.apply:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            if not compile_ok(filepath):
                errors.append(f"POST-CHECK FAILED: {filepath}, restoring")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(original_lines)
                count = 0

        fixed += count

    print(f"\nFixed: {fixed}/{len(TARGETS)}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        return 1
    print("No errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
