#!/usr/bin/env python3
"""
Clean up generated/reproducible artifacts created by the project's
docx/pdf → markdown conversion pipeline and IDE-side historical state.

Two subcommands are exposed by ``argparse``:

- ``artifacts`` (default for backwards compatibility): remove regenerated
  ``docx/pdf → markdown`` caches and ``__pycache__`` directories. Supports an
  optional ``--max-age-days`` filter and a ``--keep-manifest`` JSON dump.

- ``ide-history``: remove historical state left behind by Cursor, Roo Code,
  Codebuddy, etc. when the workspace is reopened on a new machine or after
  prolonged inactivity. Targets are auto-discovered (only directories that
  actually exist are touched) and filtered by default to entries older than
  two weeks, mirroring the project's two-week historical-task policy.
  WorkBuddy's own historical subdirectories (traces, logs, sessions,
  audit-log, file-history, shell-snapshots, artifact-index, tasks,
  automation-backups) are also cleaned with the same age filter.

Both subcommands are read-only by default; pass ``--apply`` to actually delete.

Typical usage
-------------

    # Preview what would be cleaned from the project (no filesystem changes):

    python scripts/cleanup_generated_artifacts.py artifacts --dry-run

    # Same, for IDE history (Cursor/Roo Code/etc.), age-filtered at 14 days:

    python scripts/cleanup_generated_artifacts.py ide-history --apply \\
        --max-age-days 14 --keep-manifest reports/ide_history_manifest.json

    # Legacy invocation (kept for any existing callers):

    python scripts/cleanup_generated_artifacts.py --apply --max-age-days 14
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

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

DEFAULT_MAX_AGE_DAYS = 14


@dataclass(frozen=True)
class CleanupResult:
    """Summary of a cleanup run."""

    removed: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[Path] = field(default_factory=list)
    kept: list[Path] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def failed_count(self) -> int:
        return len(self.failed)


# ---------------------------------------------------------------------------
# Age-based filtering helpers
# ---------------------------------------------------------------------------


def _iter_files_under(p: Path) -> Iterable[Path]:
    """Yield every regular file under ``p`` (recursively).

    Unlike ``p.rglob('*')`` which returns both files and directories, this
    helper only yields files — callers never need directory entries from it.
    No sorting is applied: the caller (_partition_by_age) does not depend on
    order, and avoiding ``sorted()`` saves an O(n log n) pass on large trees.
    """
    if not p.is_dir():
        return
    for entry in p.rglob("*"):
        if entry.is_file():
            yield entry


def _partition_by_age(
    p: Path, *, max_age_days: float | None, now: float
) -> tuple[list[Path], list[Path]]:
    """Split files under ``p`` into (stale, fresh) using last mtime.

    For a directory target we operate on individual files so that a fresh file
    can keep its parent directory alive. For a file target we test it directly.
    """
    cutoff = now - (max_age_days * 86400.0) if max_age_days is not None else None
    stale: list[Path] = []
    fresh: list[Path] = []

    if p.is_file():
        try:
            mtime = p.stat().st_mtime
        except OSError:
            return [], []
        if cutoff is None or mtime < cutoff:
            stale.append(p)
        else:
            fresh.append(p)
        return stale, fresh

    for entry in _iter_files_under(p):
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            # If we cannot stat a file, treat it as fresh to avoid surprise deletes.
            fresh.append(entry)
            continue
        if cutoff is None or mtime < cutoff:
            stale.append(entry)
        else:
            fresh.append(entry)
    return stale, fresh


def _delete_files(files: Sequence[Path], *, dry_run: bool, result: CleanupResult) -> None:
    for f in files:
        if dry_run:
            logger.info("[dry-run] would remove: %s", f)
            result.removed.append(f)
            continue
        try:
            f.unlink()
        except FileNotFoundError:
            continue
        except (OSError, PermissionError) as exc:
            logger.error("failed to remove %s: %s", f, exc)
            result.failed.append(f)
        else:
            logger.info("removed %s", f)
            result.removed.append(f)


def _cleanup_empty_dirs(p: Path, *, dry_run: bool) -> int:
    """Remove empty parent directories of ``p`` once files have been deleted."""
    if not p.exists():
        return 0
    removed = 0
    # Walk bottom-up: only delete a directory if it is empty.
    for d in sorted({f.parent for f in p.rglob("*") if f.is_file()}, reverse=True):
        try:
            # Don't delete the root target itself if it has nothing left.
            if d == p:
                continue
            if any(d.iterdir()):
                continue
        except (OSError, PermissionError):
            continue
        if dry_run:
            logger.info("[dry-run] would remove empty dir: %s", d)
            continue
        try:
            d.rmdir()
        except (OSError, PermissionError) as exc:
            logger.debug("cannot rmdir %s: %s", d, exc)
            continue
        logger.info("removed empty dir %s", d)
        removed += 1
    return removed


# ---------------------------------------------------------------------------
# Existing target helpers (kept for backwards compatibility)
# ---------------------------------------------------------------------------


def rm_tree(
    p: Path,
    *,
    dry_run: bool = False,
    result: CleanupResult | None = None,
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


def rm_pycache(
    root: Path,
    *,
    dry_run: bool = False,
    max_age_days: float | None = None,
    now: float | None = None,
) -> int:
    """Remove every ``__pycache__`` directory under the project source trees.

    When ``max_age_days`` is provided, only stale caches (whose directory mtime
    is older than the cutoff) are removed. Returns the number of cache
    directories actually removed (or that would be removed in dry-run mode).
    """
    n = 0
    cutoff_time = now if now is not None else time.time()
    cutoff = cutoff_time - (max_age_days * 86400.0) if max_age_days is not None else None
    for rel in _PYCACHE_SEARCH_DIRS:
        base = root / rel
        if not base.is_dir():
            continue
        # reverse=True so children are removed before parents.
        for d in sorted(base.rglob("__pycache__"), reverse=True):
            if not d.is_dir():
                continue
            if cutoff is not None:
                # Use the cache directory's own mtime (set by Python whenever it
                # writes new bytecode). Walking the tree is not reliable: a single
                # recently-touched ``.pyc`` (e.g. an import probe) would mask every
                # other stale file inside, causing the whole cache to look "fresh".
                try:
                    latest = d.stat().st_mtime
                except OSError as exc:
                    logger.debug("cannot stat %s: %s", d, exc)
                    continue
                if latest >= cutoff:
                    logger.debug("keeping fresh cache: %s", d)
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


def collect_targets(root: Path) -> list[Path]:
    """Return the list of regenerated-artifact directories this script owns."""
    return [
        root / "review_materials" / "_md",
        root / "review_materials" / "converted",
        root / "docs" / "_converted",
    ]


def cleanup_targets_with_age(
    root: Path,
    *,
    max_age_days: float | None,
    now: float,
    dry_run: bool,
    result: CleanupResult,
) -> None:
    """Apply age-filtered cleanup to each target listed in ``collect_targets``.

    Files newer than ``max_age_days`` are added to ``result.kept`` so the
    manifest reflects what was preserved.
    """
    for target in collect_targets(root):
        if not target.exists():
            logger.debug("skip (not found): %s", target)
            continue
        stale, fresh = _partition_by_age(target, max_age_days=max_age_days, now=now)
        result.kept.extend(fresh)
        _delete_files(stale, dry_run=dry_run, result=result)
        _cleanup_empty_dirs(target, dry_run=dry_run)


# ---------------------------------------------------------------------------
# IDE history cleanup (Cursor / Roo Code / Codebuddy / VSCode)
# ---------------------------------------------------------------------------


def _user_home() -> Path:
    """Return the user's home directory in a cross-platform way."""
    return Path(os.path.expanduser("~"))


def _appdata_local(home: Path | None = None) -> Path:
    """Return ``%LOCALAPPDATA%`` (Windows: ``C:/Users/<user>/AppData/Local``).

    When *home* is given (e.g. a test sandbox), the result is derived from it
    instead of the real environment variable so that tests are hermetic.
    """
    if home is not None:
        return home / "AppData" / "Local"
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local)
    return _user_home() / "AppData" / "Local"


def _appdata_roaming(home: Path | None = None) -> Path:
    """Return ``%APPDATA%`` (Windows: ``C:/Users/<user>/AppData/Roaming``).

    When *home* is given (e.g. a test sandbox), the result is derived from it
    instead of the real environment variable so that tests are hermetic.
    """
    if home is not None:
        return home / "AppData" / "Roaming"
    roaming = os.environ.get("APPDATA")
    if roaming:
        return Path(roaming)
    return _user_home() / "AppData" / "Roaming"


def discover_ide_history_dirs(home: Path | None = None) -> list[Path]:
    """Return the list of IDE-history directories that exist on this machine.

    Each entry is a *container* whose children are individual history entries
    (workspaces, sessions, databases, log files). Empty / missing paths are
    filtered out so the script never errors out on a clean install.
    """
    home = home or _user_home()
    local = _appdata_local(home)
    roaming = _appdata_roaming(home)

    # History-style locations we know about. The list is intentionally
    # conservative: we only clean items that are unambiguously *historical*
    # state (workspaces, sessions, audit logs) or *regeneratable* (caches).
    # Backups and VSCode internal caches are deliberately excluded.
    #
    # NOTE: ``~/.codebuddy`` and ``~/.workbuddy`` are NOT included here.
    # They contain active WorkBuddy session state (CLI watchers, MCP config,
    # memory) that must never be bulk-deleted as "IDE history".
    # WorkBuddy *historical* subdirectories (traces, logs, sessions, etc.)
    # are discovered separately by ``discover_workbuddy_history_dirs()``
    # which targets only specific subdirectories, not the root.
    candidates: list[Path] = [
        # Cursor
        home / ".cursor" / "projects",  # per-workspace sessions & state
        home / ".cursor" / "ai-tracking",  # AI code-tracking SQLite DB
        home / ".cursor" / "cleanup-logs",  # chat cleanup history
        home / ".cursor" / "skills-cursor",  # built-in skill snapshots
        home / ".cursor" / "logs",  # Cursor's own logs
        roaming / "Cursor" / "logs",  # Cursor's main log directory
        roaming / "Cursor" / "CachedConfigurations",  # re-discoverable config snapshots
        # Roo Code standalone install paths (rare; most users install as
        # a VS Code / Cursor extension — handled below via dynamic discovery)
        home / ".roo",
        home / ".roo-code",
        roaming / "Roo Code",
        roaming / "Roo-Code",
        local / "Roo Code",
        local / "Programs" / "Roo-Code",
        # Vanilla VSCode (only workspaceStorage/logs which are not user-critical)
        roaming / "Code" / "logs",
        roaming / "Code" / "CachedConfigurations",
    ]

    # ---- Dynamic discovery: Roo Code as a VS Code / Cursor extension ----
    # When Roo Code (rooveterinaryinc.roo-cline) is installed as an extension,
    # its per-task conversation history and model cache live under the host
    # editor's globalStorage directory, not in the standalone paths above.
    #
    # We scan for any directory matching ``*roo*`` under globalStorage to
    # support versioned extension IDs and future renames. Only the ``tasks``
    # (conversation history) and ``cache`` (regeneratable model lists)
    # subdirectories are added — ``settings`` is user config and is excluded.
    for editor_name in ("Cursor", "Code"):
        gs_root = roaming / editor_name / "User" / "globalStorage"
        if gs_root.is_dir():
            for entry in gs_root.iterdir():
                if not entry.is_dir():
                    continue
                name_lower = entry.name.lower()
                if "roo" in name_lower:
                    tasks_dir = entry / "tasks"
                    cache_dir = entry / "cache"
                    if tasks_dir.is_dir():
                        candidates.append(tasks_dir)
                    if cache_dir.is_dir():
                        candidates.append(cache_dir)
    # Safety guard: never touch any path containing a .workbuddy or
    # .codebuddy component — these are active WorkBuddy state directories.
    _PROTECTED_NAMES = {".workbuddy", ".codebuddy"}
    return [
        p
        for p in candidates
        if p.exists() and not any(part in _PROTECTED_NAMES for part in p.parts)
    ]


def discover_workbuddy_history_dirs(home: Path | None = None) -> list[Path]:
    """Return the list of WorkBuddy *historical* subdirectories that exist.

    Unlike ``discover_ide_history_dirs`` which skips ``~/.workbuddy``
    entirely (to protect active state), this function targets only specific
    subdirectories within ``~/.workbuddy`` that contain historical or
    regeneratable data:

    - ``sessions/``      – per-PID session metadata JSONs
    - ``traces/``        – per-PID trace logs (largest historical consumer)
    - ``audit-log/``     – date-based audit JSONL logs (``state.json`` and
                           ``manifest.jsonl`` are kept because they are
                           actively maintained and always fresh)
    - ``file-history/``  – per-session file version snapshots
    - ``logs/``          – date-named log directories and standalone log files
    - ``shell-snapshots/`` – timestamped shell environment snapshots
    - ``artifact-index/``  – per-session artifact index JSONs
    - ``tasks/``           – per-session task records
    - ``automation-backups/`` – timestamped automation backup JSONs

    Active state (``workbuddy.db``, ``memory/``, ``skills/``, ``settings.json``,
    identity files, ``binaries/``, ``connectors/``, etc.) is never included.
    """
    wb_root = (home or _user_home()) / ".workbuddy"
    if not wb_root.is_dir():
        return []
    candidates: list[Path] = [
        wb_root / "sessions",
        wb_root / "traces",
        wb_root / "audit-log",
        wb_root / "file-history",
        wb_root / "logs",
        wb_root / "shell-snapshots",
        wb_root / "artifact-index",
        wb_root / "tasks",
        wb_root / "automation-backups",
    ]
    return [p for p in candidates if p.is_dir()]


def _ide_entries(target: Path) -> list[Path]:
    """Return the list of history entries under ``target``.

    - Directories (e.g. ``~/.cursor/projects/<workspace-id>``) become entries.
    - Files (e.g. ``ai-code-tracking.db``) are themselves entries.
    - Symlinks are followed via ``iterdir``.
    """
    if not target.exists():
        return []
    if target.is_file():
        return [target]
    try:
        return sorted(p for p in target.iterdir())
    except (OSError, PermissionError) as exc:
        logger.debug("cannot iterate %s: %s", target, exc)
        return []


def cleanup_ide_history(
    *,
    max_age_days: float = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
    dry_run: bool = False,
    result: CleanupResult | None = None,
    home: Path | None = None,
    targets: list[Path] | None = None,
) -> CleanupResult:
    """Delete IDE-history entries older than ``max_age_days``.

    Entries older than the cutoff are removed wholesale (a workspace directory
    or a single tracking DB file). Fresh entries (typical when the user just
    opened Cursor) are kept.

    ``targets`` may be pre-supplied (e.g. by a caller that already invoked
    ``discover_ide_history_dirs``) to avoid redundant filesystem I/O.
    """
    result = result or CleanupResult(removed=[], skipped=[], failed=[], kept=[])
    now = now if now is not None else time.time()
    cutoff = now - (max_age_days * 86400.0)
    if targets is None:
        targets = discover_ide_history_dirs(home=home)
    if not targets:
        logger.info("no IDE-history directories detected on this machine")
        return result

    logger.info("scanning %d IDE-history location(s)", len(targets))
    for target in targets:
        entries = _ide_entries(target)
        if not entries:
            logger.debug("no entries under %s", target)
            continue
        for entry in entries:
            try:
                mtime = entry.stat().st_mtime
            except OSError as exc:
                logger.debug("cannot stat %s: %s", entry, exc)
                continue
            if mtime >= cutoff:
                result.kept.append(entry)
                logger.debug(
                    "keeping fresh entry: %s (%.1f days)",
                    entry,
                    (now - mtime) / 86400.0,
                )
                continue
            age_days = (now - mtime) / 86400.0
            if dry_run:
                logger.info("[dry-run] would remove: %s (%.1f days old)", entry, age_days)
                result.removed.append(entry)
                continue
            try:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            except FileNotFoundError:
                continue
            except (OSError, PermissionError) as exc:
                logger.error("failed to remove %s: %s", entry, exc)
                result.failed.append(entry)
                continue
            logger.info("removed %s (%.1f days old)", entry, age_days)
            result.removed.append(entry)
    return result


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def write_keep_manifest(
    path: Path,
    *,
    kept: Sequence[Path],
    removed: Sequence[Path],
    failed: Sequence[Path],
    max_age_days: float | None,
    dry_run: bool,
    scope: str,
) -> None:
    """Persist the run summary as JSON so downstream tooling can reconcile."""
    payload = {
        "scope": scope,
        "timestamp": time.time(),
        "dry_run": dry_run,
        "max_age_days": max_age_days,
        "kept": [str(p) for p in kept],
        "removed": [str(p) for p in removed],
        "failed": [str(p) for p in failed],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote keep-manifest: %s", path)


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------


def _resolve_max_age_days(args: argparse.Namespace) -> float | None:
    """Resolve the effective ``max_age_days`` from CLI + env.

    Order of precedence: explicit CLI flag > environment variable > default
    (off). For ``ide-history`` the caller may pass a default to enable the
    two-week policy out of the box.
    """
    cli_value = getattr(args, "max_age_days", None)
    if cli_value is not None:
        return float(cli_value)
    env_value = os.environ.get("CLEANUP_MAX_AGE_DAYS")
    if env_value is not None and env_value.strip():
        try:
            return float(env_value)
        except ValueError:
            logger.warning("CLEANUP_MAX_AGE_DAYS is not numeric (%s); ignoring", env_value)
    fallback = getattr(args, "_default_max_age_days", None)
    return fallback


def _common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
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
    return parser


def _ensure_apply_or_dry_run(args: argparse.Namespace) -> tuple[bool, bool]:
    """Validate that at least one of --apply / --dry-run is set.

    Returns ``(dry_run, exit_early)`` where ``exit_early=True`` means the
    script should exit cleanly without doing anything.
    """
    if not args.apply and not args.dry_run:
        logger.info("nothing to do: pass --apply to delete or --dry-run to preview.")
        return True, True
    return not args.apply, False


# ---------------------------------------------------------------------------
# Subcommand: artifacts (project-local cleanup)
# ---------------------------------------------------------------------------


def run_artifacts(argv: Sequence[str] | None = None) -> int:
    parser = _common_parser(
        description=(
            "Remove regenerated docx→md artifacts and __pycache__. "
            "Pass --max-age-days (or set CLEANUP_MAX_AGE_DAYS) for the "
            "two-week historical-task policy."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (default: parent of this script).",
    )
    parser.add_argument(
        "--max-age-days",
        type=float,
        default=None,
        help=("Only delete items older than N days. Disabled by default."),
    )
    parser.add_argument(
        "--keep-manifest",
        type=Path,
        default=None,
        help=("Optional path to write a JSON manifest of items that were kept."),
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    root: Path = args.root.resolve()
    if not root.is_dir():
        logger.error("root is not a directory: %s", root)
        return 2

    dry_run, exit_early = _ensure_apply_or_dry_run(args)
    if exit_early:
        return 0

    max_age_days = _resolve_max_age_days(args)
    if max_age_days is not None:
        logger.info(
            "age filter enabled: removing only items older than %.2f days",
            max_age_days,
        )

    result = CleanupResult(removed=[], skipped=[], failed=[], kept=[])
    now = time.time()

    if max_age_days is None:
        # Legacy semantics: nuke each target directory entirely.
        for target in collect_targets(root):
            rm_tree(target, dry_run=dry_run, result=result)
        pycache_removed = rm_pycache(root, dry_run=dry_run)
    else:
        cleanup_targets_with_age(
            root,
            max_age_days=max_age_days,
            now=now,
            dry_run=dry_run,
            result=result,
        )
        pycache_removed = rm_pycache(
            root,
            dry_run=dry_run,
            max_age_days=max_age_days,
            now=now,
        )

    logger.info(
        "__pycache__ directories: %d %s",
        pycache_removed,
        "would be removed" if dry_run else "removed",
    )
    logger.info(
        "summary: removed=%d kept=%d failed=%d",
        result.removed_count,
        len(result.kept),
        result.failed_count,
    )

    if args.keep_manifest is not None:
        write_keep_manifest(
            args.keep_manifest,
            kept=result.kept,
            removed=result.removed,
            failed=result.failed,
            max_age_days=max_age_days,
            dry_run=dry_run,
            scope="artifacts",
        )
    return 0 if result.failed_count == 0 else 1


# ---------------------------------------------------------------------------
# Subcommand: ide-history (Cursor / Roo Code / etc.)
# ---------------------------------------------------------------------------


def run_ide_history(argv: Sequence[str] | None = None) -> int:
    parser = _common_parser(
        description=(
            "Remove IDE history (Cursor / Roo Code / VSCode workspace snapshots) "
            "older than the configured threshold. The two-week policy is the "
            "default; override with --max-age-days=0 to wipe everything."
        ),
    )
    parser.add_argument(
        "--max-age-days",
        type=float,
        default=None,
        help=(
            "Only delete entries older than N days. "
            f"Defaults to {DEFAULT_MAX_AGE_DAYS} days when --apply is used."
        ),
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=None,
        help=(
            "Override the user's home directory (used in tests). Defaults to $USERPROFILE / $HOME."
        ),
    )
    parser.add_argument(
        "--keep-manifest",
        type=Path,
        default=None,
        help=("Optional path to write a JSON manifest of items that were kept."),
    )
    args = parser.parse_args(argv)
    args._default_max_age_days = float(DEFAULT_MAX_AGE_DAYS)
    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    dry_run, exit_early = _ensure_apply_or_dry_run(args)
    if exit_early:
        return 0

    max_age_days = _resolve_max_age_days(args)
    assert max_age_days is not None  # default set above

    logger.info(
        "IDE history age filter: removing entries older than %.2f days",
        max_age_days,
    )

    # Discover IDE history targets and WorkBuddy historical subdirectories.
    # Both are cleaned with the same age-based logic. WorkBuddy dirs are
    # discovered separately because they live inside ~/.workbuddy which is
    # protected by _PROTECTED_NAMES in discover_ide_history_dirs().
    targets = discover_ide_history_dirs(home=args.home)
    wb_targets = discover_workbuddy_history_dirs(home=args.home)
    targets.extend(wb_targets)

    result = cleanup_ide_history(
        max_age_days=max_age_days,
        dry_run=dry_run,
        home=args.home,
        targets=targets,
    )

    logger.info(
        "ide-history summary: locations=%d removed=%d kept=%d failed=%d",
        len(targets),
        result.removed_count,
        len(result.kept),
        result.failed_count,
    )

    if args.keep_manifest is not None:
        write_keep_manifest(
            args.keep_manifest,
            kept=result.kept,
            removed=result.removed,
            failed=result.failed,
            max_age_days=max_age_days,
            dry_run=dry_run,
            scope="ide-history",
        )
    return 0 if result.failed_count == 0 else 1


# ---------------------------------------------------------------------------
# Top-level CLI: legacy (no subcommand) + dispatcher
# ---------------------------------------------------------------------------


def _print_top_help() -> None:
    sys.stdout.write(
        "Usage:\n"
        "  cleanup_generated_artifacts.py artifacts [options]\n"
        "  cleanup_generated_artifacts.py ide-history [options]\n\n"
        "  (Legacy) cleanup_generated_artifacts.py [options]\n"
        "      -> equivalent to 'artifacts' subcommand for backwards compat.\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # No arguments at all -> show help.
    if not argv or argv[0] in {"-h", "--help"}:
        _print_top_help()
        return 0
    if argv[0] == "artifacts":
        return run_artifacts(argv[1:])
    if argv[0] == "ide-history":
        return run_ide_history(argv[1:])
    # Anything else: treat as legacy (no subcommand) invocation.
    return run_artifacts(argv)


if __name__ == "__main__":
    sys.exit(main())
