#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up generated/reproducible artifacts created by the project's
docx/pdf → markdown conversion pipeline.

Targets
-------
- ``<repo>/review_materials/_md``        produced by ``convert_review_materials.py``
- ``<repo>/review_materials/converted``  legacy output from ``convert_review_to_md.py``
- ``<repo>/docs/_converted``             converted docs cache (already in .gitignore)
- ``__pycache__`` under ``scripts``, ``tests``, ``tools``, ``skills``, ``docs``
  (NOT under any virtual environment at the repo root)

This script is intentionally read-only by default. Pass ``--apply`` to
actually remove files. Use ``--dry-run`` to preview.
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

LOG_FORMAT = "%(asctime)s [%(levelname)s] cleanup_artifacts: %(message)s"
logger = logging.getLogger("cleanup_artifacts")

# Subtrees where removing __pycache__ is safe. Virtual environments
# are excluded on purpose: they live under .venv/, not under these paths.
_PYCACHE_SEARCH_DIRS: tuple[str, ...] = (
    "scripts",
    "tests",
    "tools",
    "skills",
    "docs",
)


@dataclass(frozen=True)
class CleanupResult:
    """Summary of a cleanup run."""

    removed: List[Path]
    skipped: List[Path]
    failed: List[Path]

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def failed_count(self) -> int:
        return len(self.failed)


def rm_tree(
    p: Path,
    *,
    dry_run: bool = False,
    result: Optional[CleanupResult] = None,
) -> None:
    """Recursively delete ``p`` if it exists. Errors are logged, not raised."""
    if not p.exists():
        logger.debug("skip (not found): %s", p)
        return

    if dry_run:
        logger.info("[dry-run] would remove: %s", p)
        if result is not None:
            result.removed.append(p)
        return

    try:
        shutil.rmtree(p)
    except (OSError, PermissionError) as exc:
        logger.error("failed to remove %s: %s", p, exc)
        if result is not None:
            result.failed.append(p)
        return

    logger.info("removed %s", p)
    if result is not None:
        result.removed.append(p)


def rm_pycache(root: Path, *, dry_run: bool = False) -> int:
    """Remove every ``__pycache__`` directory under the project source trees.

    Returns
    -------
    int
        Number of cache directories actually removed (or that *would* be
        removed in dry-run mode).
    """
    n = 0
    for rel in _PYCACHE_SEARCH_DIRS:
        base = root / rel
        if not base.is_dir():
            continue
        # reverse=True so children are removed before parents.
        for d in sorted(base.rglob("__pycache__"), reverse=True):
            if not d.is_dir():
                continue
            if dry_run:
                logger.info("[dry-run] would remove: %s", d)
                n += 1
                continue
            try:
                shutil.rmtree(d)
            except (OSError, PermissionError) as exc:
                logger.error("failed to remove %s: %s", d, exc)
                continue
            logger.info("removed %s", d)
            n += 1
    return n


def collect_targets(root: Path) -> List[Path]:
    """Return the list of regenerated-artifact directories this script owns."""
    return [
        root / "review_materials" / "_md",
        root / "review_materials" / "converted",
        root / "docs" / "_converted",
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cleanup_generated_artifacts",
        description="Remove regenerated docx→md artifacts and __pycache__.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (default: parent of this script).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files. Without this flag, the script is a no-op.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be removed without touching the filesystem.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity (default: %(default)s).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    root: Path = args.root.resolve()
    if not root.is_dir():
        logger.error("root is not a directory: %s", root)
        return 2

    if not args.apply and not args.dry_run:
        logger.info(
            "nothing to do: pass --apply to delete or --dry-run to preview."
        )
        return 0

    dry_run = not args.apply
    if dry_run:
        logger.info("DRY-RUN mode: no files will be removed.")

    result = CleanupResult(removed=[], skipped=[], failed=[])
    for target in collect_targets(root):
        rm_tree(target, dry_run=dry_run, result=result)

    pycache_removed = rm_pycache(root, dry_run=dry_run)
    logger.info("__pycache__ directories: %d %s", pycache_removed, "would be removed" if dry_run else "removed")
    logger.info(
        "summary: removed=%d failed=%d",
        result.removed_count,
        result.failed_count,
    )
    return 0 if result.failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
