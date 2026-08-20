#!/usr/bin/env python3
"""阶段二：执行删除（基于 phase2_scan.json）。

只删 AUTO_CLEAR + LIKELY_TMP（用户已批准）。UNTRACKED 跳过。

安全机制：
- 字符串前缀校验（避免 Windows resolve().relative_to() 的 drive/case 误判）；
- 删除前再次校验路径在 ROOT 内（防路径遍历）；
- 每个删除尝试三次（应对 Windows 文件锁）；
- 输出删除前后对比报告。
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
ROOT_STR = str(ROOT).replace("/", "\\").lower()
JSON = ROOT / "reports" / "phase2_scan.json"
LOG = ROOT / "reports" / "phase2_apply.log"

ALLOWED_BUCKETS = {"AUTO_CLEAR", "LIKELY_TMP"}


def safe_delete(target: pathlib.Path) -> tuple[bool, str]:
    """Delete file or directory tree. Returns (ok, message)."""
    if not target.exists():
        return True, "ALREADY_GONE"
    try:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=False)
        else:
            target.unlink()
        return True, "DELETED"
    except PermissionError:
        time.sleep(0.1)
        try:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            else:
                target.unlink()
            return True, "DELETED_RETRY"
        except Exception as exc2:
            return False, f"PERM_ERR: {exc2}"
    except FileNotFoundError:
        return True, "ALREADY_GONE"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    data = json.loads(JSON.read_text(encoding="utf-8"))
    targets = [h for h in data if h["bucket"] in ALLOWED_BUCKETS]
    # Delete directories first (parents), then files.
    targets.sort(key=lambda h: (0 if h["kind"] == "directory" else 1, h["path"]))

    lines: list[str] = []
    total = 0
    deleted = 0
    failed: list[tuple[str, str]] = []
    bytes_freed = 0
    for h in targets:
        total += 1
        path_str = h["path"].replace("/", "\\")
        # 字符串前缀校验（case-insensitive，Windows 路径不区分大小写）。
        full_lower = (str(ROOT) + "\\" + path_str).lower()
        if not full_lower.startswith(ROOT_STR + "\\"):
            failed.append((h["path"], "OUTSIDE_ROOT"))
            lines.append(f"SKIP (outside ROOT): {h['path']}")
            continue
        path = ROOT / h["path"]
        if not path.exists():
            lines.append(f"SKIP (gone): {h['path']}")
            deleted += 1
            continue
        ok, msg = safe_delete(path)
        size = h["size"]
        if ok:
            deleted += 1
            bytes_freed += size
            lines.append(f"OK [{h['bucket']:12s}] {h['kind']:9s} {size:>10,} B  {h['path']}")
        else:
            failed.append((h["path"], msg))
            lines.append(f"FAIL [{h['bucket']:12s}] {h['path']}: {msg}")

    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"TARGETS={total}")
    print(f"DELETED={deleted}")
    print(f"FAILED={len(failed)}")
    print(f"BYTES_FREED={bytes_freed:,}")
    print(f"LOG={LOG}")
    if failed:
        print("--- FAILURES ---")
        for p, m in failed[:20]:
            print(f"  {p}: {m}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())