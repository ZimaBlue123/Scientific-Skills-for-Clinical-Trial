#!/usr/bin/env python3
"""Broad f-string cleanup: remove f-prefix from all f-strings without placeholders
across skills/ directory. Uses regex-based approach with py_compile safety checks.

Usage:
    python scripts/fix_fstrings_broad.py          # dry-run
    python scripts/fix_fstrings_broad.py --apply   # write changes
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

# Targets extracted from pyflakes output: (relative_path, [line_numbers])
TARGETS = {
    "clinical-decision-support/scripts/biomarker_classifier.py": [198, 219, 224, 243, 250],
    "clinical-decision-support/scripts/create_cohort_tables.py": [300, 301],
    "clinical-decision-support/scripts/generate_survival_analysis.py": [313, 339],
    "clinical-reports/scripts/check_deidentification.py": [290, 300],
    "clinical-reports/scripts/validate_case_report.py": [222],
    "clinpgx-database/scripts/query_clinpgx.py": [101],
    "cosmic-database/scripts/download_cosmic.py": [157],
    "exploratory-data-analysis/scripts/eda_analyzer.py": [540, 543],
    "fda-database/scripts/fda_examples.py": [37, 66, 89, 103, 212, 290, 294],
    "markitdown/scripts/convert_with_ai.py": [144],
    "perplexity-search/scripts/perplexity_search.py": [262],
    "perplexity-search/scripts/setup_env.py": [154],
    "scikit-learn/scripts/clustering_analysis.py": [186, 193],
    "statistical-analysis/scripts/assumption_checks.py": [471, 482],
    "treatment-plans/scripts/timeline_generator.py": [364],
    "treatment-plans/scripts/validate_treatment_plan.py": [227, 236],
}


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


def fix_fstring_line(line):
    result = re.sub(r'\bf"""([^{]*?)"""', r'"""\1"""', line)
    result = re.sub(r"\bf'''([^{]*?)'''", r"'''\1'''", result)
    result = re.sub(r'\bf"((?:[^{"\\]|\\.)*)"', r'"\1"', result)
    result = re.sub(r"\bf'((?:[^{'\\]|\\.)*)'", r"'\1'", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Broad f-string cleanup [{mode}] ===\n")

    total_fixed = 0
    errors = []

    for rel_path, line_numbers in sorted(TARGETS.items()):
        filepath = SKILLS_DIR / rel_path
        if not filepath.exists():
            errors.append(f"FILE NOT FOUND: {filepath}")
            continue

        if not compile_ok(filepath):
            errors.append(f"PRE-CHECK FAILED: {filepath}")
            continue

        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        original_lines = lines[:]

        count = 0
        for lineno in line_numbers:
            idx = lineno - 1
            if idx < 0 or idx >= len(lines):
                errors.append(f"  {rel_path} L{lineno}: out of range")
                continue
            original = lines[idx]
            fixed = fix_fstring_line(original)
            if fixed != original:
                lines[idx] = fixed
                count += 1
                print(f"  {rel_path} L{lineno}: fixed")
            else:
                errors.append(f"  {rel_path} L{lineno}: no match")

        if count > 0 and args.apply:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            if not compile_ok(filepath):
                errors.append(f"POST-CHECK FAILED: {filepath}, restoring")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(original_lines)
                count = 0

        total_fixed += count

    target_count = sum(len(v) for v in TARGETS.values())
    print(f"\nFixed: {total_fixed}/{target_count}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        return 1
    print("No errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
