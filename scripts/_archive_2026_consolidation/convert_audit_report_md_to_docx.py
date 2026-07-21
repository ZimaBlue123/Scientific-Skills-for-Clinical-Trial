from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_md_to_docx():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "md_to_docx.py"
    spec = importlib.util.spec_from_file_location("md_to_docx", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    review = root / "review_materials"
    candidates = sorted(review.glob("审核报告_YDSWX*.md"))
    if not candidates:
        raise SystemExit(f"no matching md under {review}")

    md_path = candidates[0]
    out_path = md_path.with_suffix(".docx")

    mod = _load_md_to_docx()
    mod.md_to_docx(md_path.read_text(encoding="utf-8"), out_path)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
