#!/usr/bin/env python3
"""Fix vendored skills cosmetic warnings: f-strings without placeholders and redundant re-imports.

Safety:
- Every file is py_compile validated before and after modification.
- Only modifies files under skills/.
- Dry-run mode by default; pass --apply to write changes.
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

# ---------- f-string targets ----------
# (relative_path_from_skills, line_number)
FSTRING_TARGETS = [
    ("analytical-method-validation/scripts/check_accuracy_precision.py", 347),
    ("analytical-method-validation/scripts/check_detection_limits.py", 256),
    ("analytical-method-validation/scripts/check_detection_limits.py", 262),
    ("analytical-method-validation/scripts/check_response.py", 244),
    ("analytical-method-validation/scripts/compare_methods.py", 193),
    ("analytical-method-validation/scripts/plan_validation.py", 111),
    ("analytical-method-validation/scripts/plan_validation.py", 166),
    ("diffdock/scripts/setup_check.py", 32),
    ("document-skills-docx/scripts/document.py", 296),
    ("document-skills-docx/scripts/document.py", 377),
    ("document-skills-docx/scripts/utilities.py", 178),
    ("pathogen-variant-surveillance/scripts/lineage_prevalence.py", 335),
    ("pathogen-variant-surveillance/scripts/reporting_lag.py", 222),
    ("pathogen-variant-surveillance/scripts/reporting_lag.py", 229),
    ("pathogen-variant-surveillance/scripts/resolve_lineage.py", 200),
    ("scientific-slides/scripts/generate_schematic_ai.py", 964),
    ("timesfm-forecasting/examples/covariates-forecasting/demo_covariates.py", 212),
    ("timesfm-forecasting/examples/covariates-forecasting/demo_covariates.py", 290),
    ("timesfm-forecasting/examples/covariates-forecasting/demo_covariates.py", 369),
    ("timesfm-forecasting/examples/covariates-forecasting/demo_covariates.py", 371),
    ("timesfm-forecasting/examples/global-temperature/generate_gif.py", 138),
    ("timesfm-forecasting/scripts/check_system.py", 234),
    ("timesfm-forecasting/scripts/check_system.py", 245),
    ("timesfm-forecasting/scripts/check_system.py", 319),
]

# ---------- redundant re-import targets ----------
# (relative_path_from_skills, line_number, exact_stripped_content)
REIMPORT_TARGETS = [
    ("diffdock/scripts/setup_check.py", 21, "import sys"),
    ("scientific-slides/scripts/generate_slide_image_ai.py", 356, "import re"),
]


def compile_ok(filepath: Path) -> bool:
    """Return True if the file compiles without error."""
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


def fix_fstring_line(line: str) -> str:
    """Remove the f prefix from f-strings that contain no {} placeholders."""
    result = re.sub(r'\bf"""([^{]*?)"""', r'"""\1"""', line)
    result = re.sub(r"\bf'''([^{]*?)'''", r"'''\1'''", result)
    result = re.sub(r'\bf"((?:[^{"\\]|\\.)*)"', r'"\1"', result)
    result = re.sub(r"\bf'((?:[^{'\\]|\\.)*)'", r"'\1'", result)
    return result


def process_file(filepath: Path, line_numbers: list, apply: bool) -> tuple:
    """Fix f-string issues at specific line numbers. Returns (count_fixed, errors)."""
    errors = []

    if not compile_ok(filepath):
        errors.append(f"  PRE-CHECK FAILED: {filepath} does not compile before fix")
        return 0, errors

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original_lines = lines[:]
    count = 0
    for lineno in line_numbers:
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            errors.append(f"  Line {lineno} out of range in {filepath}")
            continue

        original = lines[idx]
        fixed = fix_fstring_line(original)

        if fixed != original:
            lines[idx] = fixed
            count += 1
            print(f"  L{lineno}: {original.strip()}")
            print(f"      -> {fixed.strip()}")
        else:
            errors.append(f"  L{lineno}: no f-string without placeholder found: {original.strip()}")

    if count > 0 and apply:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

        if not compile_ok(filepath):
            errors.append(f"  POST-CHECK FAILED: {filepath} does not compile after fix!")
            # Restore original
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(original_lines)
            return 0, errors

    return count, errors


def fix_reimport(filepath: Path, lineno: int, expected_stripped: str, apply: bool) -> tuple:
    """Remove a redundant re-import line. Returns (success, errors)."""
    errors = []

    if not compile_ok(filepath):
        errors.append(f"  PRE-CHECK FAILED: {filepath}")
        return False, errors

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    idx = lineno - 1
    if idx < 0 or idx >= len(lines):
        errors.append(f"  Line {lineno} out of range in {filepath}")
        return False, errors

    actual = lines[idx]
    if actual.strip() != expected_stripped:
        errors.append(f"  L{lineno}: expected '{expected_stripped}', got '{actual.strip()}'")
        return False, errors

    print(f"  L{lineno}: removing '{actual.strip()}'")
    original_lines = lines[:]
    lines.pop(idx)

    if apply:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

        if not compile_ok(filepath):
            errors.append(f"  POST-CHECK FAILED after removing L{lineno}")
            # Restore
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(original_lines)
            return False, errors

    return True, errors


def main():
    parser = argparse.ArgumentParser(description="Fix vendored skills cosmetic warnings")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Fix vendored skills warnings [{mode}] ===\n")

    # Group f-string targets by file
    file_lines = {}
    for rel_path, lineno in FSTRING_TARGETS:
        file_lines.setdefault(rel_path, []).append(lineno)

    total_fixed = 0
    all_errors = []

    # Fix f-strings
    print("--- F-string fixes ---")
    for rel_path in sorted(file_lines):
        line_numbers = file_lines[rel_path]
        filepath = SKILLS_DIR / rel_path
        if not filepath.exists():
            all_errors.append(f"  FILE NOT FOUND: {filepath}")
            continue
        print(f"\n{rel_path}:")
        count, errors = process_file(filepath, line_numbers, args.apply)
        total_fixed += count
        all_errors.extend(errors)

    # Fix redundant re-imports
    print("\n--- Redundant re-import fixes ---")
    reimport_fixed = 0
    for rel_path, lineno, content in REIMPORT_TARGETS:
        filepath = SKILLS_DIR / rel_path
        if not filepath.exists():
            all_errors.append(f"  FILE NOT FOUND: {filepath}")
            continue
        print(f"\n{rel_path}:")
        ok, errors = fix_reimport(filepath, lineno, content, args.apply)
        if ok:
            reimport_fixed += 1
        all_errors.extend(errors)

    # Summary
    print("\n=== Summary ===")
    print(f"F-string fixes: {total_fixed}/{len(FSTRING_TARGETS)}")
    print(f"Re-import fixes: {reimport_fixed}/{len(REIMPORT_TARGETS)}")
    if all_errors:
        print(f"\nErrors ({len(all_errors)}):")
        for e in all_errors:
            print(e)
        return 1
    else:
        print("No errors.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
