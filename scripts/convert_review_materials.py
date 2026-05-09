from __future__ import annotations

from pathlib import Path

from markitdown import MarkItDown
from striprtf.striprtf import rtf_to_text


def main() -> int:
    src = Path(__file__).resolve().parents[1] / "review_materials"
    out = src / "_md"
    out.mkdir(exist_ok=True)

    md = MarkItDown()

    ok = 0
    failed = 0
    for p in sorted(src.iterdir()):
        if p.is_dir():
            continue
        if p.suffix.lower() not in {".docx", ".rtf", ".pdf", ".txt", ".xlsx", ".pptx"}:
            continue
        try:
            if p.suffix.lower() == ".rtf":
                # markitdown currently may pass through raw RTF markup; use striprtf for fidelity.
                text = rtf_to_text(p.read_text(encoding="utf-8", errors="ignore")).strip()
            else:
                r = md.convert(str(p))
                text = (r.text_content or "").strip()
            ok += 1
        except Exception as e:
            text = f"[CONVERSION_ERROR] {e!r}"
            failed += 1

        (out / f"{p.name}.md").write_text(text, encoding="utf-8")
        print(f"converted\t{p.name}\tlen={len(text)}")

    print(f"done\tok={ok}\tfailed={failed}\tout={out}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
