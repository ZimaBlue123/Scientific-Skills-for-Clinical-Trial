#!/usr/bin/env python3
"""Repair single-byte UTF-8 corruption where a sequence-final byte became ``?``.

Symptom
-------
Files that fail ``bytes.decode("utf-8")`` with a context such as::

    b'\\xe2\\x86?Markdown'      # should be b'\\xe2\\x86\\x92' -> U+2192 RIGHT ARROW
    b'\\xe2\\x94?  \\xe2\\x94\\x9c'  # should be b'\\xe2\\x94\\x80' -> U+2500 BOX DRAWINGS LIGHT HORIZONTAL

Root cause: a tool round-tripped the text through a lossy encoding and replaced the
final continuation byte of every multi-byte sequence with ASCII ``?`` (0x3F).

Strategy
--------
Rather than guessing blindly, every candidate repair is resolved against a table of
*known-good* sequences observed in this repository, then re-validated: the repaired
buffer must decode as strict UTF-8. Anything that cannot be resolved confidently is
reported instead of silently mangled.

Usage
-----
    python scripts/_tools/repair_truncated_multibyte_sequences.py [--write]

Without ``--write`` the tool runs in dry-run mode (report only), which is the safe
default for CI and for human review.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Scanned extensions only; binary formats are intentionally skipped so that a
# legitimate 0x3F inside, say, a PNG is never touched.
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml", ".ps1", ".cmd", ".rst", ".tex"}

# Directories that are never repaired in place.
EXCLUDED_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".ruff_cache", ".workbuddy"}

# Map of <truncated prefix bytes> -> <correct full sequence>.
# Each entry was verified against surrounding context in the affected files.
# Seed table for prefixes that may not occur often enough elsewhere to be learned.
# Values are verified against the surrounding context in the affected documents.
KNOWN_SEQUENCES: dict[bytes, bytes] = {
    b"\xe2\x94": b"\xe2\x94\x80",  # -| BOX DRAWINGS LIGHT HORIZONTAL (tree drawing)
    b"\xe2\x9c": b"\xe2\x9c\x93",  # check mark
}


def _decode_valid(data: bytes) -> str | None:
    """Strict UTF-8 decode that returns ``None`` instead of raising."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def learn_prefix_completions(files: list[Path]) -> dict[bytes, Counter]:
    """Learn ``<2-byte utf-8 prefix> -> most common valid 3-byte sequence``.

    The corpus is every *clean* (decodable) text file in the repository, so the
    reconstruction is inferred from the project's own vocabulary instead of being
    guessed. Example: ``b"\\xe7\\xbb"`` is completed most often as ``b"\\xe7\\xbb\\x93"``
    (``结``) in this repository, so a truncated ``b"\\xe7\\xbb?"`` is restored to it.
    """
    counts: dict[bytes, Counter] = {}
    for path in files:
        data = path.read_bytes()
        if _decode_valid(data) is None:
            continue
        idx = 0
        length = len(data)
        while idx < length - 2:
            lead = data[idx]
            if 0xE0 <= lead <= 0xEF:  # start of a 3-byte sequence
                prefix = data[idx:idx + 2]
                third = data[idx + 2]
                if 0x80 <= third <= 0xBF:
                    counts.setdefault(prefix, Counter())[data[idx:idx + 3]] += 1
                    idx += 3
                    continue
            idx += 1
    return counts


def _resolve(prefix: bytes, learned: dict[bytes, Counter]) -> bytes | None:
    """Return the most probable completion for a truncated *prefix*."""
    if prefix in KNOWN_SEQUENCES:
        return KNOWN_SEQUENCES[prefix]
    candidates = learned.get(prefix)
    if not candidates:
        return None
    return candidates.most_common(1)[0][0]


def repair_bytes(data: bytes, learned: dict[bytes, Counter] | None = None) -> tuple[bytes, list[str]]:
    """Return ``(repaired_bytes, human_readable_repairs)``.

    Each *bad* pattern is ``<incomplete utf-8 prefix> + b'?'``. In valid UTF-8 a
    multi-byte prefix can only be followed by a continuation byte (0x80-0xBF), so
    every occurrence of such a pattern is unambiguously corruption.
    """
    learned = learned or {}
    buffer = bytearray(data)
    log: list[str] = []

    # Scan for '<2-byte lead/continue>?' shapes and restore the missing final byte.
    for index in range(2, len(buffer) - 1):
        if buffer[index] != 0x3F:  # '?'
            continue
        prefix = bytes(buffer[index - 2:index])
        lead = prefix[0:1]
        if not (0xC2 <= lead[0] <= 0xEF):
            continue
        if not (0x80 <= prefix[1] <= 0xBF):
            continue
        full = _resolve(prefix, learned)
        if full is None:
            log.append(f"offset {index - 2}: unresolved prefix {prefix.hex()} (left untouched)")
            continue
        replacement_char = full.decode("utf-8")
        buffer[index - 2:index + 1] = full
        log.append(
            f"offset {index - 2}: {prefix.hex()} + '?' -> "
            f"U+{ord(replacement_char):04X} ({replacement_char!r})"
        )

    return bytes(buffer), log


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        parts = set(path.parts)
        if parts & EXCLUDED_PARTS:
            continue
        # The vendored subproject keeps its own history and conventions.
        if str(path).replace("\\", "/").startswith("scripts/clinical-automation/"):
            continue
        files.append(path)
    return sorted(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply repairs (default: dry run)")
    args = parser.parse_args(argv)

    all_files = iter_text_files(REPO_ROOT)
    learned = learn_prefix_completions(all_files)

    affected = 0
    unresolved = 0
    for path in all_files:
        data = path.read_bytes()
        if _decode_valid(data) is not None:
            continue  # already clean

        repaired, log = repair_bytes(data, learned)
        affected += 1
        print(f"\n[corrupt] {path.relative_to(REPO_ROOT)}")
        if not log:
            print("    - no known pattern matched; needs manual inspection")
            unresolved += 1
        for entry in log:
            print(f"    - {entry}")
            unresolved += entry.count("unresolved")

        try:
            repaired.decode("utf-8")  # final safety gate before writing
        except UnicodeDecodeError as exc:
            print(f"    ! still invalid after repair: {exc}")
            unresolved += 1
            continue

        if args.write:
            path.write_bytes(repaired)
            print("    -> repaired and written")

    print(f"\nScanned repository; affected files: {affected}, unresolved items: {unresolved}")
    if affected and not args.write:
        print("Dry run only. Re-run with --write to apply repairs.")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
