"""
PPTX 包完整性比对：确认改写后的文件未丢失任何内部构件（媒体、图表、
嵌入 OLE、主题、母版等），并列出各部件字节差异。

用法:
  python scripts/compare_pptx_package.py <原始.pptx> <新.pptx>
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def parts(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as z:
        return {i.filename: i.file_size for i in z.infolist()}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    a_path, b_path = Path(sys.argv[1]), Path(sys.argv[2])
    a, b = parts(a_path), parts(b_path)

    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    common = sorted(set(a) & set(b))

    print(f"原始 {a_path.name}: {len(a)} 个部件, 合计 {sum(a.values()) / 1048576:.2f} MB")
    print(f"新版 {b_path.name}: {len(b)} 个部件, 合计 {sum(b.values()) / 1048576:.2f} MB")
    print()
    print(f"仅原始存在（可能丢失）: {len(only_a)}")
    for n in only_a:
        print(f"   - {n}  ({a[n]} B)")
    print(f"仅新版存在（新增）: {len(only_b)}")
    for n in only_b:
        print(f"   + {n}  ({b[n]} B)")

    # 校验关键构件族是否存在
    for fam, pat in [
        ("媒体文件", "ppt/media/"),
        ("幻灯片", "ppt/slides/slide"),
        ("嵌入对象", "ppt/embeddings/"),
        ("图表", "ppt/charts/"),
        ("备注", "ppt/notesSlides/"),
    ]:
        na = sum(1 for k in a if k.startswith(pat))
        nb = sum(1 for k in b if k.startswith(pat))
        mark = "OK " if nb >= na else "!!! "
        print(f"{mark}{fam}: 原始 {na} -> 新版 {nb}")

    print()
    print("共有部件中大小不同的（XML 序列化差异属正常）:")
    diff = [(n, a[n], b[n]) for n in common if a[n] != b[n]]
    print(f"  共 {len(diff)} / {len(common)} 个")
    for n, sa, sb in sorted(diff, key=lambda x: -abs(x[1] - x[2]))[:15]:
        print(f"   {n}: {sa} -> {sb}  (Δ{sb - sa:+d})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
