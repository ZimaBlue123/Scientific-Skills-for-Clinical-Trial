#!/usr/bin/env python3
"""
Escape unsafe text entities in SVG text nodes.

Fixes the most common rendering failure:
- unescaped '&' in text content (e.g., "A & B")
"""

import re
import sys
from pathlib import Path


def sanitize_text_chunk(chunk: str) -> str:
    # Preserve valid XML entities, escape remaining ampersands.
    return re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", chunk)


def sanitize_svg(svg: str) -> tuple[str, int]:
    replacements = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal replacements
        original = match.group(1)
        sanitized = sanitize_text_chunk(original)
        if sanitized != original:
            replacements += 1
        return f">{sanitized}<"

    # Only sanitize text-node content between tags.
    updated = re.sub(r">([^<]*)<", repl, svg, flags=re.S)
    return updated, replacements


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 sanitize-svg-text.py <svg-file>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}")
        return 1

    content = path.read_text(encoding="utf-8")
    sanitized, count = sanitize_svg(content)
    path.write_text(sanitized, encoding="utf-8")
    print(f"Sanitized {count} text segment(s): {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
