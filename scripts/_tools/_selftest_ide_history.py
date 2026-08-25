#!/usr/bin/env python3
"""Self-test for ``cleanup_generated_artifacts.py ide-history``.

Builds a fake ``$HOME`` tree containing Cursor / Roo Code / Codebuddy-shaped
entries with mixed ages (stale + fresh) and asserts ``ide-history`` deletes
exactly the stale ones, keeps the fresh ones, and writes a manifest when
requested.

The script never touches the real user home: it points ``--home`` at a
sandbox directory and verifies behaviour entirely against mock state.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "cleanup_generated_artifacts.py"
# Use the system temp directory instead of .workbuddy/ to avoid
# triggering bulk-delete safety guards that protect .workbuddy paths.
SANDBOX = Path(tempfile.gettempdir()) / "ide_history_selftest"
PYTHON = sys.executable


def _stamp(path: Path, age_days: float) -> None:
    mtime = time.time() - age_days * 86400.0
    os.utime(path, (mtime, mtime))


def _run(args: list[str], *, home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(SCRIPT), "ide-history", *args, "--home", str(home)],
        capture_output=True,
        text=True,
    )


def _build_sandbox() -> None:
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    SANDBOX.mkdir(parents=True)
    # Mirror the layout `discover_ide_history_dirs` looks at.
    projects = SANDBOX / ".cursor" / "projects"
    cleanup_logs = SANDBOX / ".cursor" / "cleanup-logs"
    skills_cursor = SANDBOX / ".cursor" / "skills-cursor"
    ai_tracking = SANDBOX / ".cursor" / "ai-tracking"
    codebuddy = SANDBOX / ".codebuddy"
    roo_home = SANDBOX / ".roo"
    for d in (projects, cleanup_logs, skills_cursor, ai_tracking, codebuddy, roo_home):
        d.mkdir(parents=True)

    # Stale + fresh workspace dirs.
    (projects / "old_workspace").mkdir()
    (projects / "fresh_workspace").mkdir()
    _stamp(projects / "old_workspace", age_days=30)
    _stamp(projects / "fresh_workspace", age_days=2)

    # Stale + fresh log files.
    stale_log = cleanup_logs / "old.log"
    fresh_log = cleanup_logs / "new.log"
    stale_log.write_text("x", encoding="utf-8")
    fresh_log.write_text("x", encoding="utf-8")
    _stamp(stale_log, age_days=40)
    _stamp(fresh_log, age_days=1)

    # ai-tracking contains a single SQLite-shaped DB file.
    db = ai_tracking / "ai-code-tracking.db"
    db.write_bytes(b"\x00" * 1024)
    _stamp(db, age_days=20)  # stale

    # Cursor skills-cursor: 1 stale entry.
    (skills_cursor / "old_skill").mkdir()
    _stamp(skills_cursor / "old_skill", age_days=50)

    # Codebuddy home: 1 fresh + 1 stale entry.
    (codebuddy / "old_state").mkdir()
    (codebuddy / "fresh_state").mkdir()
    _stamp(codebuddy / "old_state", age_days=25)
    _stamp(codebuddy / "fresh_state", age_days=3)

    # Roo Code home: 1 stale.
    (roo_home / "history.json").write_text("{}", encoding="utf-8")
    _stamp(roo_home / "history.json", age_days=45)

    # ---- WorkBuddy historical subdirectories ----
    wb = SANDBOX / ".workbuddy"
    for sub in (
        "sessions",
        "traces",
        "audit-log",
        "file-history",
        "logs",
        "shell-snapshots",
        "artifact-index",
        "tasks",
        "automation-backups",
    ):
        (wb / sub).mkdir(parents=True)

    # sessions: stale + fresh PID-named JSON files
    old_session = wb / "sessions" / "99999.json"
    fresh_session = wb / "sessions" / "88888.json"
    old_session.write_text("{}", encoding="utf-8")
    fresh_session.write_text("{}", encoding="utf-8")
    _stamp(old_session, age_days=30)
    _stamp(fresh_session, age_days=1)

    # traces: stale + fresh per-PID directories
    (wb / "traces" / "99999").mkdir()
    (wb / "traces" / "88888").mkdir()
    trace_old = wb / "traces" / "99999" / "trace_old.json"
    trace_fresh = wb / "traces" / "88888" / "trace_fresh.json"
    trace_old.write_text("{}", encoding="utf-8")
    trace_fresh.write_text("{}", encoding="utf-8")
    _stamp(wb / "traces" / "99999", age_days=30)
    _stamp(wb / "traces" / "88888", age_days=1)

    # audit-log: stale date file + fresh state.json (must be kept)
    old_audit = wb / "audit-log" / "2026-06-15.jsonl"
    fresh_state = wb / "audit-log" / "state.json"
    old_audit.write_text("[]", encoding="utf-8")
    fresh_state.write_text("{}", encoding="utf-8")
    _stamp(old_audit, age_days=30)
    _stamp(fresh_state, age_days=0)

    # logs: stale date-named dir + fresh log file
    (wb / "logs" / "2026-06-15").mkdir()
    fresh_log_wb = wb / "logs" / "AppStartup.log"
    fresh_log_wb.write_text("startup", encoding="utf-8")
    _stamp(wb / "logs" / "2026-06-15", age_days=30)
    _stamp(fresh_log_wb, age_days=0)

    # shell-snapshots: 1 stale
    old_snap = wb / "shell-snapshots" / "snapshot-bash-old.sh"
    old_snap.write_text("# shell", encoding="utf-8")
    _stamp(old_snap, age_days=25)

    # Active WorkBuddy state that must NEVER be cleaned
    (wb / "memory").mkdir()
    (wb / "memory" / "MEMORY.md").write_text("# Memory", encoding="utf-8")
    _stamp(wb / "memory" / "MEMORY.md", age_days=30)  # old but protected


def _expected_state_after_apply_age14() -> dict:
    """Map of path -> True=should exist, False=should be removed.

    Note: ``.codebuddy`` entries are protected by the safety guard in
    ``discover_ide_history_dirs`` and must survive cleanup even when stale.
    WorkBuddy's ``memory/`` directory is NOT a cleanup target (only
    historical subdirectories are) and must also survive.
    """
    return {
        # IDE history
        ".cursor/projects/old_workspace": False,
        ".cursor/projects/fresh_workspace": True,
        ".cursor/cleanup-logs/old.log": False,
        ".cursor/cleanup-logs/new.log": True,
        ".cursor/ai-tracking/ai-code-tracking.db": False,
        ".cursor/skills-cursor/old_skill": False,
        ".codebuddy/old_state": True,  # protected — must NOT be cleaned
        ".codebuddy/fresh_state": True,
        ".roo/history.json": False,
        # WorkBuddy history
        ".workbuddy/sessions/99999.json": False,
        ".workbuddy/sessions/88888.json": True,
        ".workbuddy/traces/99999": False,
        ".workbuddy/traces/88888": True,
        ".workbuddy/audit-log/2026-06-15.jsonl": False,
        ".workbuddy/audit-log/state.json": True,  # fresh — kept
        ".workbuddy/logs/2026-06-15": False,
        ".workbuddy/logs/AppStartup.log": True,  # fresh — kept
        ".workbuddy/shell-snapshots/snapshot-bash-old.sh": False,
        # WorkBuddy active state — never a target
        ".workbuddy/memory/MEMORY.md": True,
    }


def _assert_path(rel: str, should_exist: bool) -> bool:
    exists = (SANDBOX / rel).exists()
    return exists == should_exist


def _all_expected(plan: dict) -> bool:
    return all(_assert_path(rel, exists) for rel, exists in plan.items())


def case_no_args_exits_cleanly() -> bool:
    """No flags = no-op, exit 0, FS untouched."""
    _build_sandbox()
    proc = _run([], home=SANDBOX)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return False
    return _all_expected(
        {
            ".cursor/projects/old_workspace": True,
            ".cursor/projects/fresh_workspace": True,
            ".cursor/cleanup-logs/old.log": True,
            ".cursor/ai-tracking/ai-code-tracking.db": True,
            ".codebuddy/old_state": True,
            ".roo/history.json": True,
            ".workbuddy/sessions/99999.json": True,
            ".workbuddy/traces/99999/trace_old.json": True,
            ".workbuddy/audit-log/2026-06-15.jsonl": True,
            ".workbuddy/memory/MEMORY.md": True,
        }
    )


def case_dry_run_preserves_fs() -> bool:
    """Dry-run must NOT touch the filesystem: every fixture still exists."""
    _build_sandbox()
    proc = _run(["--dry-run", "--max-age-days=14"], home=SANDBOX)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return False
    return _all_expected(
        {
            ".cursor/projects/old_workspace": True,
            ".cursor/projects/fresh_workspace": True,
            ".cursor/cleanup-logs/old.log": True,
            ".cursor/cleanup-logs/new.log": True,
            ".cursor/ai-tracking/ai-code-tracking.db": True,
            ".cursor/skills-cursor/old_skill": True,
            ".codebuddy/old_state": True,
            ".codebuddy/fresh_state": True,
            ".roo/history.json": True,
            ".workbuddy/sessions/99999.json": True,
            ".workbuddy/sessions/88888.json": True,
            ".workbuddy/traces/99999/trace_old.json": True,
            ".workbuddy/traces/88888/trace_fresh.json": True,
            ".workbuddy/audit-log/2026-06-15.jsonl": True,
            ".workbuddy/audit-log/state.json": True,
            ".workbuddy/logs/2026-06-15": True,
            ".workbuddy/logs/AppStartup.log": True,
            ".workbuddy/shell-snapshots/snapshot-bash-old.sh": True,
            ".workbuddy/memory/MEMORY.md": True,
        }
    )


def case_apply_removes_only_stale() -> bool:
    _build_sandbox()
    proc = _run(["--apply", "--max-age-days=14"], home=SANDBOX)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return False
    return _all_expected(_expected_state_after_apply_age14())


def case_keep_manifest_ok() -> bool:
    _build_sandbox()
    manifest = SANDBOX / "manifest.json"
    proc = _run(
        [
            "--apply",
            "--max-age-days=14",
            "--keep-manifest",
            str(manifest),
        ],
        home=SANDBOX,
    )
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return False
    if not manifest.exists():
        return False
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return (
        payload.get("scope") == "ide-history"
        and payload.get("max_age_days") == 14.0
        and payload.get("dry_run") is False
        and any("fresh_workspace" in k for k in payload["kept"])
        and any("old_workspace" in r for r in payload["removed"])
        and any("88888.json" in k for k in payload["kept"])  # WB fresh session
        and any("99999.json" in r for r in payload["removed"])  # WB stale session
        and any("state.json" in k for k in payload["kept"])  # WB audit state
    )


def case_missing_home_silent_skip() -> bool:
    """No IDE dirs in sandbox: command exits 0 and reports removed=0."""
    empty_home = SANDBOX / "empty_home"
    if empty_home.exists():
        shutil.rmtree(empty_home)
    empty_home.mkdir()
    proc = _run(["--dry-run", "--max-age-days=14"], home=empty_home)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return False
    return "removed=0" in (proc.stdout + proc.stderr)


CASES: list[tuple] = [
    ("no args = no-op", case_no_args_exits_cleanly),
    ("dry-run preserves filesystem", case_dry_run_preserves_fs),
    ("apply removes only stale", case_apply_removes_only_stale),
    ("keep-manifest writes JSON", case_keep_manifest_ok),
    ("empty home silent skip", case_missing_home_silent_skip),
]


def main() -> int:
    failures = []
    for name, fn in CASES:
        try:
            ok = bool(fn())
        except Exception as exc:  # noqa: BLE001
            ok = False
            failures.append(f"[FAIL] {name} :: raised {exc!r}")
            continue
        if not ok:
            failures.append(f"[FAIL] {name}")
        else:
            print(f"[PASS] {name}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"\nAll {len(CASES)} ide-history self-test cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
