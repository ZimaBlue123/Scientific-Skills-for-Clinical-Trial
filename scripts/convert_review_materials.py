from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert review materials to Markdown via markitdown."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(Path(__file__).resolve().parents[1]),
        help="Project root path (default: inferred from this script location)",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="review_materials",
        help="Input directory relative to root unless absolute path is provided",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="_converted_md",
        help="Output subdirectory under input dir unless absolute path is provided",
    )
    args = parser.parse_args()

    try:
        from markitdown import MarkItDown
    except Exception as e:  # pragma: no cover
        print(f"ERROR: markitdown import failed: {e}", file=sys.stderr)
        return 2

    project_root = Path(args.root)
    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = project_root / input_dir

    if not input_dir.exists():
        print(f"ERROR: directory not found: {input_dir}", file=sys.stderr)
        return 2

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = input_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [
            p
            for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".docx", ".xlsx", ".pdf"}
        ]
    )
    if not files:
        print("ERROR: no .docx/.xlsx/.pdf files found", file=sys.stderr)
        return 2

    md = MarkItDown()
    failures: list[tuple[Path, str]] = []

    for p in files:
        try:
            result = md.convert(str(p))
            text = result.text_content or ""
            out_path = out_dir / f"{p.name}.md"
            out_path.write_text(text, encoding="utf-8")
            print(f"OK: {p.name} -> {out_path.name}")
        except Exception as e:  # pragma: no cover
            failures.append((p, str(e)))
            print(f"FAIL: {p.name}: {e}", file=sys.stderr)

    if failures:
        print("\nFailures:", file=sys.stderr)
        for p, msg in failures:
            print(f"- {p.name}: {msg}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

