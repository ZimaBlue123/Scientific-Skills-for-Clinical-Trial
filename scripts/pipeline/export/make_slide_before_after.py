"""把两份 PPTX 的同一页渲染成上下对照图（可指定裁切区域），便于目视 diff。

用法:
  python make_slide_before_after.py <旧pptx> <新pptx> <页码> <输出png>
         [--crop L,T,R,B (英寸)] [--title-old 文字] [--title-new 文字]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RENDER = HERE / "render_slide_highres.py"


def render(pptx: str, page: int, out: Path, w: int = 3200, h: int = 1800) -> None:
    subprocess.run(
        [sys.executable, str(RENDER), pptx, str(page), str(out), str(w), str(h)],
        check=True,
    )


def _system_font_dir() -> Path:
    """Return the OS font directory without hard-coding a drive letter."""
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        return Path(windir) / "Fonts"
    return Path("/usr/share/fonts")  # POSIX fallback (Linux/macOS)


def load_font(size: int):
    font_dir = _system_font_dir()
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "arial.ttf"):
        p = font_dir / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass  # Intentional: font file unreadable; try the next candidate below.
    return ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old_pptx")
    ap.add_argument("new_pptx")
    ap.add_argument("page", type=int)
    ap.add_argument("out_png")
    ap.add_argument("--crop", default=None, help="L,T,R,B 单位英寸")
    ap.add_argument("--title-old", default="修改前")
    ap.add_argument("--title-new", default="修改后")
    ap.add_argument("--width", type=int, default=3200)
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="ba_"))
    try:
        a = tmp / "old.png"
        b = tmp / "new.png"
        render(args.old_pptx, args.page, a, args.width, int(args.width * 9 / 16))
        render(args.new_pptx, args.page, b, args.width, int(args.width * 9 / 16))

        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        if args.crop:
            l, t, r, bt = (float(x) for x in args.crop.split(","))
            ppi = ia.size[1] / 7.5
            box = (int(l * ppi), int(t * ppi), int(r * ppi), int(bt * ppi))
            ia, ib = ia.crop(box), ib.crop(box)

        bar = 64
        W = max(ia.width, ib.width)
        H = bar + ia.height + bar + ib.height
        canvas = Image.new("RGB", (W, H), "white")
        canvas.paste(ia, (0, bar))
        canvas.paste(ib, (0, bar + ia.height + bar))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, 0, W, bar], fill=(192, 0, 0))
        d.rectangle([0, bar + ia.height, W, bar + ia.height + bar], fill=(192, 0, 0))
        f = load_font(40)
        d.text((20, 12), args.title_old, fill="white", font=f)
        d.text((20, bar + ia.height + 12), args.title_new, fill="white", font=f)
        out = Path(args.out_png)
        out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out)
        print("saved", out, canvas.size)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
