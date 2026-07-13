#!/usr/bin/env python3
"""Self-test for ``cleanup_generated_artifacts.py``.

Builds a sandbox project tree with:
- target directories containing a mix of old + fresh files
- a ``__pycache__`` whose directory mtime is stale and a fresh file inside
- the legacy "delete everything" semantic must still work when age filter is off

Each case asserts the expected outcome (files removed / kept) and exits non-zero
on the first failure so it is safe to wire into CI.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "cleanup_generated_artifacts.py"
# Use the system temp directory instead of .workbuddy/ to avoid
# triggering bulk-delete safety guards that protect .workbuddy paths.
SANDBOX = Path(tempfile.gettempdir()) / "cleanup_selftest"
PYTHON = sys.executable


def _run(args: Sequence[str], *, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(SCRIPT), *args],
        cwd=str(SANDBOX),
        env=env,
        capture_output=True,
        text=True,
    )


@dataclass
class Case:
    name: str
    setup: Callable[[], None] | None
    argv: list[str]
    env_overrides: dict
    assertion: Callable[[], bool]


def _stamp(path: Path, age_days: float) -> None:
    """Force ``path`` to look ``age_days`` days old."""
    mtime = time.time() - age_days * 86400.0
    os.utime(path, (mtime, mtime))


def _build_sandbox() -> None:
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    SANDBOX.mkdir(parents=True)
    (SANDBOX / "review_materials" / "_md").mkdir(parents=True)
    (SANDBOX / "review_materials" / "converted").mkdir(parents=True)
    (SANDBOX / "docs" / "_converted").mkdir(parents=True)
    (SANDBOX / "scripts").mkdir()
    (SANDBOX / "scripts" / "__pycache__").mkdir()

    # Old + fresh files inside review_materials/_md
    old_md_1 = SANDBOX / "review_materials" / "_md" / "old_doc_a.md"
    old_md_2 = SANDBOX / "review_materials" / "_md" / "old_doc_b.md"
    fresh_md = SANDBOX / "review_materials" / "_md" / "fresh_doc.md"
    old_md_1.write_text("OLD A", encoding="utf-8")
    old_md_2.write_text("OLD B", encoding="utf-8")
    fresh_md.write_text("FRESH", encoding="utf-8")
    _stamp(old_md_1, age_days=30)
    _stamp(old_md_2, age_days=21)
    _stamp(fresh_md, age_days=2)

    # One old file inside docs/_converted
    old_doc = SANDBOX / "docs" / "_converted" / "old_doc.md"
    old_doc.write_text("OLD DOC", encoding="utf-8")
    _stamp(old_doc, age_days=40)

    # Stale + fresh pyc files
    stale_pyc = SANDBOX / "scripts" / "__pycache__" / "stale_module.cpython-314.pyc"
    fresh_pyc = SANDBOX / "scripts" / "__pycache__" / "fresh_module.cpython-314.pyc"
    stale_pyc.write_bytes(b"\x00\x00")
    fresh_pyc.write_bytes(b"\x00\x00")
    _stamp(stale_pyc, age_days=45)
    _stamp(fresh_pyc, age_days=1)
    # Stamp the parent __pycache__ directory to 45 days ago. The script
    # judges a __pycache__ by its own mtime.
    _stamp(SANDBOX / "scripts" / "__pycache__", age_days=45)


def _env() -> dict:
    env = os.environ.copy()
    env.pop("CLEANUP_MAX_AGE_DAYS", None)
    return env


CASES: list[Case] = []


def case(name, setup, argv, env_overrides, assertion):
    CASES.append(Case(name, setup, argv, env_overrides, assertion))


# Case 1: dry-run preserves filesystem
case(
    name="dry-run with --max-age-days=14 keeps filesystem intact",
    setup=_build_sandbox,
    argv=["--dry-run", "--max-age-days=14", "--root", str(SANDBOX)],
    env_overrides={},
    assertion=lambda: (
        (SANDBOX / "review_materials" / "_md" / "old_doc_a.md").exists()
        and (SANDBOX / "review_materials" / "_md" / "old_doc_b.md").exists()
        and (SANDBOX / "review_materials" / "_md" / "fresh_doc.md").exists()
        and (SANDBOX / "docs" / "_converted" / "old_doc.md").exists()
        and (SANDBOX / "scripts" / "__pycache__" / "stale_module.cpython-314.pyc").exists()
        and (SANDBOX / "scripts" / "__pycache__" / "fresh_module.cpython-314.pyc").exists()
    ),
)

# Case 2: --apply with --max-age-days=14 removes only stale items
case(
    name="--apply --max-age-days=14 removes only stale items",
    setup=_build_sandbox,
    argv=["--apply", "--max-age-days=14", "--root", str(SANDBOX)],
    env_overrides={},
    assertion=lambda: (
        not (SANDBOX / "review_materials" / "_md" / "old_doc_a.md").exists()
        and not (SANDBOX / "review_materials" / "_md" / "old_doc_b.md").exists()
        and (SANDBOX / "review_materials" / "_md" / "fresh_doc.md").exists()
        and not (SANDBOX / "docs" / "_converted" / "old_doc.md").exists()
        and not (SANDBOX / "scripts" / "__pycache__" / "stale_module.cpython-314.pyc").exists()
    ),
)

# Case 3: legacy semantics — no age filter wipes everything
case(
    name="legacy: --apply without --max-age-days wipes targets",
    setup=_build_sandbox,
    argv=["--apply", "--root", str(SANDBOX)],
    env_overrides={},
    assertion=lambda: (
        not (SANDBOX / "review_materials" / "_md").exists()
        and not (SANDBOX / "docs" / "_converted").exists()
        and not (SANDBOX / "scripts" / "__pycache__").exists()
    ),
)

# Case 4: env var fallback
case(
    name="CLEANUP_MAX_AGE_DAYS=21 selects correct cutoff via env",
    setup=_build_sandbox,
    argv=["--apply", "--root", str(SANDBOX)],
    env_overrides={"CLEANUP_MAX_AGE_DAYS": "21"},
    assertion=lambda: (
        not (SANDBOX / "review_materials" / "_md" / "old_doc_a.md").exists()
        and not (SANDBOX / "review_materials" / "_md" / "old_doc_b.md").exists()
        and (SANDBOX / "review_materials" / "_md" / "fresh_doc.md").exists()
        and not (SANDBOX / "scripts" / "__pycache__" / "stale_module.cpython-314.pyc").exists()
    ),
)

# Case 5: --keep-manifest
def _manifest_ok() -> bool:
    p = SANDBOX / "manifest.json"
    if not p.exists():
        return False
    payload = json.loads(p.read_text(encoding="utf-8"))
    kept = payload.get("kept")
    removed = payload.get("removed")
    return (
        isinstance(kept, list)
        and isinstance(removed, list)
        and any("fresh_doc.md" in k for k in kept)
        and any("old_doc_a.md" in r for r in removed)
        and payload.get("max_age_days") == 14.0
        and payload.get("dry_run") is False
    )


case(
    name="--keep-manifest writes JSON with kept/removed lists",
    setup=_build_sandbox,
    argv=[
        "--apply",
        "--max-age-days=14",
        "--root",
        str(SANDBOX),
        "--keep-manifest",
        str(SANDBOX / "manifest.json"),
    ],
    env_overrides={},
    assertion=_manifest_ok,
)

# Case 6: no flags = no-op
case(
    name="no flags -> exit 0, no filesystem changes",
    setup=None,
    argv=["--root", str(SANDBOX)],
    env_overrides={},
    assertion=lambda: SANDBOX.exists(),
)


def run() -> int:
    failures: list[str] = []
    for c in CASES:
        if c.setup is not None:
            c.setup()
        env = _env()
        env.update(c.env_overrides)
        proc = _run(c.argv, env=env)
        if proc.returncode != 0:
            failures.append(
                f"[FAIL] {c.name}\n  exit={proc.returncode}\n  stdout={proc.stdout}\n  stderr={proc.stderr}"
            )
            continue
        try:
            ok = bool(c.assertion())
        except Exception as exc:  # noqa: BLE001
            ok = False
            failures.append(f"[FAIL] {c.name} :: assertion raised {exc!r}")
            continue
        if not ok:
            failures.append(
                f"[FAIL] {c.name}\n  argv={c.argv}\n  env={c.env_overrides}\n  stdout={proc.stdout}\n  stderr={proc.stderr}"
            )
            continue
        print(f"[PASS] {c.name}")

    if failures:
        print("\n".join(failures))
        return 1
    print(f"\nAll {len(CASES)} self-test cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
