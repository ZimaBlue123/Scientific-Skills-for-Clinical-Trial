#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build sanitized copies of every ``*.md`` file under a source folder.

Each output file is named ``<sha1(original_filename)[:12]>.md`` and a
``manifest.json`` is written alongside it, mapping the safe filename
back to the original name and reporting the size in bytes.

Usage
-----
    py -3 scripts/make_safe_md_copies.py
    py -3 scripts/make_safe_md_copies.py --src review_materials/_md --out review_materials/_md/_safe
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

LOG_FORMAT = "%(asctime)s [%(levelname)s] make_safe_md: %(message)s"
logger = logging.getLogger("make_safe_md_copies")

ENCODING = "utf-8"
HASH_PREFIX_LEN = 12
SAFE_SUBDIR = "_safe"
MANIFEST_NAME = "manifest.json"


@dataclass(frozen=True)
class CopyRecord:
    safe_relpath: str
    original_name: str
    bytes: int


def _safe_name(original_name: str) -> str:
    """Return a stable, anonymized filename for the given original name."""
    digest = hashlib.sha1(original_name.encode("utf-8", "replace")).hexdigest()
    return f"{digest[:HASH_PREFIX_LEN]}.md"


def _is_target(p: Path) -> bool:
    """A target is a top-level .md file that does not start with ``_``."""
    return p.is_file() and p.suffix.lower() == ".md" and not p.name.startswith("_")


def make_safe_copies(
    src_dir: Path,
    out_dir: Path,
    *,
    manifest_path: Optional[Path] = None,
) -> List[CopyRecord]:
    """Copy each ``*.md`` file in ``src_dir`` to ``out_dir`` under a safe name.

    Returns the list of produced records. Failures on individual files
    are logged and skipped; the overall run continues.
    """
    if not src_dir.exists() or not src_dir.is_dir():
        raise FileNotFoundError(f"src directory not found: {src_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path is None:
        manifest_path = src_dir / MANIFEST_NAME

    records: List[CopyRecord] = []
    failures: List[tuple[Path, str]] = []

    for p in sorted(src_dir.glob("*.md")):
        if not _is_target(p):
            logger.debug("skip (not a target): %s", p.name)
            continue
        try:
            text = p.read_text(encoding=ENCODING, errors="replace")
        except OSError as exc:
            logger.error("read failed for %s: %s", p, exc)
            failures.append((p, str(exc)))
            continue

        safe_name = _safe_name(p.name)
        safe_path = out_dir / safe_name
        try:
            safe_path.write_text(text, encoding=ENCODING)
        except OSError as exc:
            logger.error("write failed for %s: %s", safe_path, exc)
            failures.append((p, str(exc)))
            continue

        records.append(
            CopyRecord(
                safe_relpath=str(Path(SAFE_SUBDIR) / safe_name),
                original_name=p.name,
                bytes=p.stat().st_size,
            )
        )
        logger.info("copied %s -> %s", p.name, safe_name)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps([r.__dict__ for r in records], ensure_ascii=False, indent=2),
        encoding=ENCODING,
    )
    logger.info(
        "wrote %d records (failures=%d) to %s",
        len(records),
        len(failures),
        manifest_path,
    )
    return records


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make_safe_md_copies",
        description="Copy *.md files to a sanitized folder with a manifest.",
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "review_materials" / "_md",
        help="Source directory containing the .md files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: <src>/_safe).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest path (default: <src>/manifest.json).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    src: Path = args.src.resolve()
    out: Path = (args.out or (src / SAFE_SUBDIR)).resolve()
    manifest: Path = (args.manifest or (src / MANIFEST_NAME)).resolve()

    try:
        records = make_safe_copies(src, out, manifest_path=manifest)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2

    print(f"wrote {len(records)} files; manifest={manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
