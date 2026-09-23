"""Audit project-owned Python sources for robustness smells.

Scope: repository-owned code only (``scripts/`` excluding the vendored
``scripts/clinical-automation/`` subtree, ``tests/`` and root-level modules).
Vendored trees are intentionally skipped so upstream code stays byte-identical.

Checks performed (AST based, no execution):
    1. bare-except        -- ``except:`` without an exception type
    2. silent-swallow     -- ``except Exception: pass`` / ``continue``
    3. open-no-encoding   -- ``open(...)`` without ``encoding=``
    4. mutable-default    -- ``def f(arg=[] / {})``
    5. subprocess-shell   -- ``subprocess.*(..., shell=True)``
    6. os-system          -- ``os.system(...)``
    7. hardcoded-abs-path -- literal ``C:\\\\Users\\\\...`` style paths

Usage:
    python scripts/audit_robustness_smells.py            # human readable
    python scripts/audit_robustness_smells.py --json     # machine readable
"""

from __future__ import annotations

import warnings

warnings.warn(
    "This module is deprecated as of Phase 4 Pipeline refactoring. Please use the new `scripts.pipeline` package instead.",
    DeprecationWarning,
    stacklevel=2
)


import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDORED = "clinical-automation"

# Literals that are legitimate even though they look like absolute paths.
ALLOWED_ABS_PATH = re.compile(r"^[A-Za-z]:\\$|^/$")

# ``<Receiver>.open(...)`` where the receiver is a third-party object whose
# ``open`` is a document/decoder factory, not the builtin text-file opener.
LIB_RECEIVERS = {
    "Image",  # Pillow
    "fitz",  # PyMuPDF
    "pymupdf",
    "pdfplumber",
    "tarfile",
    "zipfile",
    "wave",
    "sndhdr",
    "Document",
    "Workbook",
}

# Builtin ``open`` second positional argument / ``mode=`` keyword values that
# imply binary IO, where ``encoding=`` is meaningless (and rejected by CPython).
BINARY_MODE = re.compile(r"b")


def iter_owned_python_files() -> list[Path]:
    """Collect repository-owned ``*.py`` files, excluding vendored trees."""
    roots: list[Path] = [REPO_ROOT / "scripts", REPO_ROOT / "tests"]
    files: list[Path] = []

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if VENDORED in path.parts:
                continue
            files.append(path)

    for path in REPO_ROOT.glob("*.py"):
        files.append(path)

    # Stable, de-duplicated output.
    return sorted({p.resolve() for p in files})


def _is_silent_handler(node: ast.ExceptHandler) -> bool:
    """True when the handler body swallows the error without any action."""
    body = [n for n in node.body if not isinstance(n, ast.Pass)]
    if not body:
        return True
    if len(body) == 1 and isinstance(body[0], ast.Continue):
        return True
    return False


def _is_builtin_open(node: ast.Call) -> bool:
    """True only for the builtin text-file opener (not ``Image.open`` etc.)."""
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr != "open":
            return False
        base = func.value
        return not (isinstance(base, ast.Name) and base.id in LIB_RECEIVERS)
    return isinstance(func, ast.Name) and func.id == "open"


def _is_binary_open(node: ast.Call) -> bool:
    """True when the call opens in binary mode, where ``encoding=`` is invalid."""
    for kw in node.keywords:
        if (
            kw.arg == "mode"
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, str)
        ):
            return bool(BINARY_MODE.search(kw.value.value))
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        mode = node.args[1].value
        if isinstance(mode, str):
            return bool(BINARY_MODE.search(mode))
    return False


def _literal_abs_paths(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if re.match(r"^[A-Za-z]:\\", value) and not ALLOWED_ABS_PATH.match(value):
                lines.append(getattr(node, "lineno", 0))
    return sorted(set(lines))


def audit_file(path: Path) -> list[dict[str, object]]:
    """Return the list of smells found in a single file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return [{"file": str(path), "line": 0, "kind": "syntax-error", "detail": "unparsable"}]

    findings: list[dict[str, object]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "kind": "bare-except",
                        "detail": "except: without type",
                    }
                )
            elif _is_silent_handler(node):
                name = getattr(node.type, "id", None) or getattr(node.type, "attr", "Exception")
                findings.append(
                    {
                        "file": str(path),
                        "line": node.lineno,
                        "kind": "silent-swallow",
                        "detail": f"except {name}: pass",
                    }
                )

        elif isinstance(node, ast.Call):
            func = node.func
            fname = getattr(func, "id", None) or getattr(func, "attr", None)

            if fname == "open" and _is_builtin_open(node) and not _is_binary_open(node):
                if not any(kw.arg == "encoding" for kw in node.keywords):
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "kind": "open-no-encoding",
                            "detail": "open() without encoding=",
                        }
                    )
            elif fname == "system":
                base = getattr(func, "value", None)
                if getattr(base, "id", None) == "os":
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "kind": "os-system",
                            "detail": "os.system()",
                        }
                    )
            elif fname in {"run", "Popen", "call", "check_output", "check_call"}:
                if any(
                    kw.arg == "shell" and getattr(kw.value, "value", False) for kw in node.keywords
                ):
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "kind": "subprocess-shell",
                            "detail": "shell=True",
                        }
                    )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in list(node.args.defaults) + [
                d for d in node.args.kw_defaults if d is not None
            ]:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "kind": "mutable-default",
                            "detail": f"def {node.name}(...=mutable)",
                        }
                    )

    for line in _literal_abs_paths(tree):
        findings.append(
            {
                "file": str(path),
                "line": line,
                "kind": "hardcoded-abs-path",
                "detail": "literal absolute path",
            }
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit project-owned Python for robustness smells."
    )
    parser.add_argument("--json", action="store_true", help="emit machine readable JSON")
    args = parser.parse_args()

    files = iter_owned_python_files()
    all_findings: list[dict[str, object]] = []

    for path in files:
        all_findings.extend(audit_file(path))

    by_kind: dict[str, int] = {}
    for item in all_findings:
        key = str(item["kind"])
        by_kind[key] = by_kind.get(key, 0) + 1

    if args.json:
        print(
            json.dumps(
                {"files": len(files), "counts": by_kind, "findings": all_findings},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"scanned files : {len(files)}")
        print(f"total findings: {len(all_findings)}")
        for kind in sorted(by_kind):
            print(f"  {kind:<20} {by_kind[kind]}")
        for item in sorted(
            all_findings, key=lambda x: (str(x["kind"]), str(x["file"]), int(x["line"]))
        ):
            rel = Path(str(item["file"])).resolve().relative_to(REPO_ROOT)
            print(f"  [{item['kind']}] {rel}:{item['line']} - {item['detail']}")

    # Blocking severities: encoding and shell injection are correctness/safety issues.
    blocking = {"open-no-encoding", "subprocess-shell", "syntax-error"}
    return 1 if any(k in blocking for k in by_kind) else 0


if __name__ == "__main__":
    sys.exit(main())
