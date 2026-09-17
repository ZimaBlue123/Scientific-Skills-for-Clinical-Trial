"""Attribute each data point on the slide "成人乙肝疫苗接种面临的挑战与新型疫苗立题依据"
to its source PDF inside the literature library.

Scans every library PDF for the slide's specific figures and prints keyword-in-context
hits so each claim can be traced to one file.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

LIB = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "文献库-F2F Meeting"
)
OUT = Path(__file__).with_name("_slide_refs_trace.txt")

# (标签, 正则) —— 与该页 PPT 上一一对应的数据点
PATTERNS = [
    ("成人接种率14.7%", r"14\.7"),
    ("儿童覆盖率>96%", r"(9[5-9](?:\.\d+)?)\s*%"),
    ("急性乙肝发病率2.98/2.94/2.93", r"2\.9[348]"),
    ("糖尿病→肝癌/肝硬化死亡2~3倍", r"(2\s*[~～\-–—到至]\s*3\s*(?:倍|fold|times))"),
    ("母婴传播", r"(母婴传播|mother-to-child|perinatal)"),
    ("南方/欠发达地区", r"(南方|欠发达|south|less developed)"),
    ("男性高于女性", r"(男性.{0,12}高于.{0,6}女性|male.{0,30}female)"),
    ("糖尿病/肾功能不全新发感染", r"(肾功能不全|renal|kidney|diabet)"),
    ("0-1-6三剂程序/依从性", r"(0[，,\s\-–—]*1[，,\s\-–—]*6|three-dose|3-dose|completion)"),
    ("老年人效果有限", r"(≥\s*60|60 岁|65 岁|older adults|elderly|age ≥ 60)"),
]

FOCUS_DIRS = [
    LIB / "01_立题依据-流行病学与接种策略",
    LIB / "03_免疫程序-2针vs3针与依从性",
    LIB / "04_特殊人群-肾透析-糖尿病-低应答",
    LIB / "02_同类产品-CpG佐剂与对照疫苗" / "其他乙肝原研产品" / "康泰60ug乙肝疫苗临床探索",
]

_buf: list[str] = []


def out(*args) -> None:
    _buf.append(" ".join(str(a) for a in args))


for folder in FOCUS_DIRS:
    if not folder.exists():
        continue
    for pdf in sorted(folder.rglob("*.pdf")):
        rel = pdf.relative_to(LIB)
        try:
            reader = PdfReader(str(pdf))
            text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception as exc:  # noqa: BLE001
            out("=" * 90)
            out(rel, "-> READ ERROR", exc)
            continue
        flat = re.sub(r"\s+", " ", text)
        hits = []
        for label, pat in PATTERNS:
            for m in re.finditer(pat, flat, re.IGNORECASE):
                s = max(0, m.start() - 110)
                e = min(len(flat), m.end() + 110)
                hits.append((label, flat[s:e]))
        if not hits:
            continue
        out("=" * 90)
        out(f"FILE: {rel}")
        seen: set[str] = set()
        for label, ctx in hits:
            key = f"{label}|{ctx[:60]}"
            if key in seen:
                continue
            seen.add(key)
            out(f"  [{label}]")
            out(f"    ...{ctx}...")
OUT.write_text("\n".join(_buf), encoding="utf-8")
