from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "review_materials" / "_md"
    if not src.exists():
        raise SystemExit(f"missing: {src}")

    out = src / "_safe"
    out.mkdir(exist_ok=True)

    manifest: list[dict[str, object]] = []
    for p in sorted(src.glob("*.md")):
        if p.name.startswith("_"):
            continue
        sha = hashlib.sha1(p.name.encode("utf-8", "replace")).hexdigest()[:12]
        safe_name = f"{sha}.md"
        safe_path = out / safe_name

        text = p.read_text(encoding="utf-8", errors="replace")
        safe_path.write_text(text, encoding="utf-8")

        manifest.append(
            {
                "safe": str(Path("_safe") / safe_name),
                "original": p.name,
                "bytes": p.stat().st_size,
            }
        )

    (src / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(manifest)} files; manifest={src / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

