"""最终测量：第 7 页"欧洲"图各年龄段急性/慢性乙肝通报率（/10万）。

标定：y(0.00) = 基线 486（条形底边），比例尺 32.5 px = 1.00 单位。
输出：各年龄段 chronic / acute / 合计，并生成标注图供目视核对。
"""

from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SRC = HERE / "_pptx_extract" / "preview" / "slide_7_hires.png"
OUTDIR = HERE / "_pptx_extract" / "preview"
CROP = (1700, 1200, 2650, 1800)

CHRONIC = (26, 110, 50)
ACUTE = (156, 198, 90)
AGEGROUPS = ["<5", "5-14", "15-19", "20-24", "25-34", "35-44", "45-54", "55-64", ">=65"]


def close(rgb, target, tol=10):
    return all(abs(rgb[i] - target[i]) <= tol for i in range(3))


def scan_bars(chart, color, tol, min_width=8):
    w, h = chart.size
    px = chart.load()
    cols = []
    for x in range(w):
        for y in range(h):
            if close(px[x, y], color, tol):
                cols.append(x)
                break
    segs, cur = [], []
    for x in cols:
        if cur and x - cur[-1] > 4:
            segs.append(cur)
            cur = []
        cur.append(x)
    segs.append(cur) if cur else None
    bars = []
    for s in segs:
        if len(s) < min_width:
            continue
        tops = []
        for x in s:
            for y in range(h):
                if close(px[x, y], color, tol):
                    tops.append(y)
                    break
        if tops:
            bars.append((min(s), max(s), Counter(tops).most_common(1)[0][0]))
    return bars


def main():
    im = Image.open(SRC).convert("RGB")
    chart = im.crop(CROP)
    px = chart.load()

    baseline = max(
        y
        for x in range(chart.size[0])
        for y in range(chart.size[1])
        if close(px[x, y], CHRONIC, 10)
    )
    scale = 32.5

    ch_bars = scan_bars(chart, CHRONIC, 10)
    ac_bars = scan_bars(chart, ACUTE, 18)
    print("chronic bars:", ch_bars)
    print("acute bars  :", ac_bars)
    print("baseline:", baseline, " scale:", scale)

    def pair(bars):
        """把条形按 x 排序后与年龄段对齐（按 x 中心排序）。"""
        return sorted(bars, key=lambda b: (b[0] + b[1]) / 2)

    ch_sorted = pair(ch_bars)
    ac_sorted = pair(ac_bars)

    # 急性条与慢性条成对出现：同一年龄段，急性在左、慢性在右
    print("\n%-8s %9s %9s %9s" % ("age", "chronic", "acute", "total"))
    results = {}
    for i, (x0, x1, ty) in enumerate(ch_sorted):
        ag = AGEGROUPS[i] if i < len(AGEGROUPS) else f"#{i}"
        ch = (baseline - ty) / scale
        # 找与之配对的急性条：x 中心略小于慢性条
        cxc = (x0 + x1) / 2
        ac = 0.0
        for ax0, ax1, aty in ac_sorted:
            axc = (ax0 + ax1) / 2
            if -30 < axc - cxc < 0:
                ac = (baseline - aty) / scale
                break
        print("%-8s %9.2f %9.2f %9.2f" % (ag, ch, ac, ch + ac))
        results[ag] = {"chronic": round(ch, 2), "acute": round(ac, 2), "total": round(ch + ac, 2)}

    # 标注图
    dbg = chart.copy()
    d = ImageDraw.Draw(dbg)
    d.line([(0, baseline), (chart.size[0], baseline)], fill=(255, 0, 0), width=1)
    for x0, x1, ty in ch_sorted:
        d.rectangle([x0, ty, x1, baseline], outline=(0, 0, 255), width=2)
    for x0, x1, ty in ac_sorted:
        d.rectangle([x0, ty, x1, baseline], outline=(255, 140, 0), width=2)
    dbg.save(OUTDIR / "eu_chart_annotated.png")
    print("\nsaved", OUTDIR / "eu_chart_annotated.png")


if __name__ == "__main__":
    main()
