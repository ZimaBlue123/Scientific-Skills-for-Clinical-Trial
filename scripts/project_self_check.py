#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project self-check:
- Verify external commands (rsvg-convert, node, npm) availability.
- Run a minimal CLI smoke check for Python scripts under:
  - scripts/*.py
  - skills/*/scripts/*.py

The smoke check strategy is conservative:
- If a script appears to use argparse and has a __main__ guard, run `-h` and `--help`.
- Otherwise, only run a syntax compilation via `py_compile` (avoids side effects).
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
OUT_JSON = ROOT / "reports" / "self_check_report.json"
OUT_MD = ROOT / "reports" / "self_check_report.md"


@dataclass
class CmdCheck:
    name: str
    argv: list[str]
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class ScriptCheck:
    path: str
    mode: str  # help|compile_only
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    seconds: float


def _run(argv: list[str], cwd: Path | None = None, timeout_s: int = 20) -> tuple[int, str, str, float]:
    t0 = time.time()
    p = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
    )
    return p.returncode, p.stdout, p.stderr, time.time() - t0


def check_command(name: str, argv: list[str]) -> CmdCheck:
    try:
        code, out, err, _ = _run(argv, cwd=ROOT, timeout_s=10)
        return CmdCheck(name=name, argv=argv, ok=(code == 0), exit_code=code, stdout=out[:4000], stderr=err[:4000])
    except FileNotFoundError as e:
        return CmdCheck(name=name, argv=argv, ok=False, exit_code=None, stdout="", stderr=str(e))
    except subprocess.TimeoutExpired:
        return CmdCheck(name=name, argv=argv, ok=False, exit_code=None, stdout="", stderr="timeout")


def check_python_module(name: str) -> CmdCheck:
    try:
        code, out, err, _ = _run([PY, "-c", f"import {name}; print('ok')"], cwd=ROOT, timeout_s=10)
        return CmdCheck(
            name=f"python-module:{name}",
            argv=[PY, "-c", f"import {name}"],
            ok=(code == 0),
            exit_code=code,
            stdout=out[:4000],
            stderr=err[:4000],
        )
    except FileNotFoundError as e:
        return CmdCheck(name=f"python-module:{name}", argv=[PY], ok=False, exit_code=None, stdout="", stderr=str(e))
    except subprocess.TimeoutExpired:
        return CmdCheck(name=f"python-module:{name}", argv=[PY], ok=False, exit_code=None, stdout="", stderr="timeout")


def iter_python_scripts() -> list[Path]:
    scripts = []
    for p in (ROOT / "scripts").glob("*.py"):
        if p.name == Path(__file__).name:
            continue
        scripts.append(p)
    for p in (ROOT / "skills").glob("*/scripts/*.py"):
        scripts.append(p)
    return sorted(set(scripts))


def check_venv_policy() -> dict[str, object]:
    root_venv = ROOT / ".venv"
    gitignore = ROOT / ".gitignore"
    has_ignore = False
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8", errors="replace")
        # Accept common forms: ".venv/" or ".venv"
        has_ignore = (".venv/" in text) or ("\n.venv\n" in f"\n{text}\n")
    return {
        "root_venv_present": root_venv.exists(),
        "root_venv_file_count": sum(1 for _ in root_venv.rglob("*")) if root_venv.exists() else 0,
        "gitignore_has_venv_rule": has_ignore,
    }


def classify_script(p: Path) -> str:
    """
    help: has __main__ guard AND mentions argparse
    compile_only: otherwise
    """
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "compile_only"

    if "argparse" not in src:
        return "compile_only"
    if "__name__" not in src or "__main__" not in src:
        return "compile_only"

    # Basic AST check to avoid false positives on comments.
    try:
        tree = ast.parse(src, filename=str(p))
    except SyntaxError:
        return "compile_only"

    has_main_guard = False
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            # __name__ == "__main__"
            left = node.test.left
            comps = node.test.comparators
            if (
                isinstance(left, ast.Name)
                and left.id == "__name__"
                and comps
                and isinstance(comps[0], ast.Constant)
                and comps[0].value == "__main__"
            ):
                has_main_guard = True
                break

    return "help" if has_main_guard else "compile_only"


def run_script_check(p: Path) -> list[ScriptCheck]:
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    mode = classify_script(p)
    results: list[ScriptCheck] = []

    if mode == "help":
        for flag in ("-h", "--help"):
            try:
                code, out, err, sec = _run([PY, str(p), flag], cwd=ROOT, timeout_s=20)
                # help exits 0 or 2 depending on argparse config; accept both.
                ok = code in (0, 2)
                results.append(
                    ScriptCheck(
                        path=rel,
                        mode=f"help:{flag}",
                        ok=ok,
                        exit_code=code,
                        stdout=out[:4000],
                        stderr=err[:4000],
                        seconds=sec,
                    )
                )
            except subprocess.TimeoutExpired:
                results.append(
                    ScriptCheck(
                        path=rel,
                        mode=f"help:{flag}",
                        ok=False,
                        exit_code=None,
                        stdout="",
                        stderr="timeout",
                        seconds=20.0,
                    )
                )
    else:
        try:
            code, out, err, sec = _run([PY, "-m", "py_compile", str(p)], cwd=ROOT, timeout_s=20)
            results.append(
                ScriptCheck(
                    path=rel,
                    mode="compile_only",
                    ok=(code == 0),
                    exit_code=code,
                    stdout=out[:4000],
                    stderr=err[:4000],
                    seconds=sec,
                )
            )
        except subprocess.TimeoutExpired:
            results.append(
                ScriptCheck(
                    path=rel,
                    mode="compile_only",
                    ok=False,
                    exit_code=None,
                    stdout="",
                    stderr="timeout",
                    seconds=20.0,
                )
            )
    return results


def main() -> int:
    (ROOT / "reports").mkdir(exist_ok=True)

    cmd_checks = [
        check_command("rsvg-convert", ["rsvg-convert", "--version"]),
        check_command("node", ["node", "--version"]),
        check_command("npm", ["npm", "--version"]),
        check_python_module("cairosvg"),
    ]

    scripts = iter_python_scripts()
    venv_policy = check_venv_policy()
    script_results: list[ScriptCheck] = []
    for p in scripts:
        script_results.extend(run_script_check(p))

    data = {
        "root": str(ROOT),
        "python": PY,
        "venv_policy": venv_policy,
        "commands": [c.__dict__ for c in cmd_checks],
        "scripts": [s.__dict__ for s in script_results],
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    failed_cmds = [c for c in cmd_checks if not c.ok]
    failed_scripts = [s for s in script_results if not s.ok]

    lines: list[str] = []
    lines.append("# Project self-check report")
    lines.append("")
    lines.append(f"- root: `{ROOT}`")
    lines.append(f"- python: `{PY}`")
    lines.append("")

    lines.append("## External commands")
    for c in cmd_checks:
        status = "OK" if c.ok else "FAIL"
        lines.append(f"- **{c.name}**: {status} (`{' '.join(c.argv)}`)")
        if not c.ok:
            if c.stderr:
                lines.append(f"  - stderr: `{c.stderr.strip()[:300]}`")
    lines.append("")
    # Renderer capability: either rsvg-convert or cairosvg is acceptable
    renderer_ok = any(
        c.ok and c.name in {"rsvg-convert", "python-module:cairosvg"}
        for c in cmd_checks
    )
    lines.append(f"- renderer capability (rsvg-convert OR cairosvg): **{'OK' if renderer_ok else 'FAIL'}**")
    lines.append("")

    lines.append("## Virtual env policy")
    lines.append(f"- root `.venv` present: **{venv_policy['root_venv_present']}**")
    lines.append(f"- root `.venv` file count: **{venv_policy['root_venv_file_count']}**")
    lines.append(f"- `.gitignore` has `.venv` rule: **{venv_policy['gitignore_has_venv_rule']}**")
    if venv_policy["root_venv_present"]:
        lines.append("- 建议将虚拟环境移出仓库根目录（例如 `~/.venvs/`），避免误扫和性能开销。")
    lines.append("")

    lines.append("## Script smoke checks")
    lines.append(f"- total checks: **{len(script_results)}** (scripts={len(scripts)})")
    lines.append(f"- failed checks: **{len(failed_scripts)}**")
    lines.append("")

    if failed_scripts:
        lines.append("### Failures")
        for s in failed_scripts[:50]:
            lines.append(f"- `{s.path}` ({s.mode}) exit={s.exit_code} err=`{(s.stderr or '').strip()[:200]}`")
        if len(failed_scripts) > 50:
            lines.append(f"- ... and {len(failed_scripts) - 50} more")
        lines.append("")

    # Minimal CLI consistency note: ensure help is available when argparse+main guard exists.
    lines.append("## Notes")
    if failed_cmds and not renderer_ok:
        lines.append("- Renderer dependency missing: install `rsvg-convert` or ensure Python `cairosvg` is available.")
    elif failed_cmds:
        lines.append("- Some external commands are missing, but renderer is available via fallback.")
    else:
        lines.append("- External command checks passed.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if (not failed_cmds and not failed_scripts) else 2


if __name__ == "__main__":
    raise SystemExit(main())

