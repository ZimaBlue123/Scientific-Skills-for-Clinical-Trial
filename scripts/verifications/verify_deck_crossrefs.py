"""审阅核实：两处跨页矛盾的内部取证。

1) p5 声称「45–49 岁急性乙肝报告发病率最高 2.98/10万」— 核对库内 China CDC Weekly
   2005–2019 原文的实际年龄别发病率。
2) p73 称 HBV-17 CKD 研究 N=521、SPR≈70% vs 40%；p19 称 N=467、SPR 89.9% vs 81.8%
   — 核对库内 Janssen 2013 原文。
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
LIB = ROOT / "review_materials" / "文献库-F2F Meeting"
OUT = Path(__file__).with_name("_review_verify.txt")

CCDC = LIB / ("01_立题依据-流行病学与接种策略/ChinaCDCWeekly_Acute-Hepatitis-B-China-2005-2019.pdf")


def extract(path: Path) -> str:
    try:
        r = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in r.pages)
    except Exception as exc:  # noqa: BLE001
        return f"<extract failed: {exc}>"


def main() -> None:
    buf: list[str] = []

    # ---------- 1) China CDC Weekly ----------
    buf.append("=" * 80)
    buf.append("1) China CDC Weekly - Acute Hepatitis B, China, 2005-2019")
    buf.append("=" * 80)
    if not CCDC.exists():
        buf.append(f"NOT FOUND: {CCDC}")
    else:
        txt = extract(CCDC)
        buf.append(f"chars: {len(txt)}")
        for tok in ("2.98", "2.94", "2.93", "14.35", "45-49", "45–49"):
            buf.append(f"  '{tok}' 命中: {txt.count(tok)}")
        buf.append("")
        # 打印含年龄组/发病率的句子
        pat = re.compile(r"(aged?|age group|years|incidence|per 100 ?000|100,000)", re.I)
        for line in txt.split("\n"):
            line = line.strip()
            if not line or len(line) < 25:
                continue
            if pat.search(line) and re.search(r"\d", line):
                buf.append("  " + line[:300])
    buf.append("")

    # ---------- 2) Janssen 2013 / HBV-17 CKD ----------
    buf.append("=" * 80)
    buf.append("2) Janssen 2013 (HBV-17, CKD) — 核对 N 与第28周 SPR")
    buf.append("=" * 80)
    hits = sorted(LIB.rglob("*.pdf"))
    cand = [
        p
        for p in hits
        if " immunological" in p.name.lower()
        or "TLR9" in p.name
        or "CKD" in p.name
        or "23727422" in p.name
        or "Janssen" in p.name
    ]
    buf.append(f"候选文件: {[p.name for p in cand]}")
    for p in cand:
        buf.append("")
        buf.append(f"--- {p.name}")
        t = extract(p)
        for tok in (
            "521",
            "467",
            "89.9",
            "81.8",
            "70%",
            "40%",
            "seroprotection",
            "randomized",
            "enrolled",
        ):
            buf.append(f"    '{tok}' 命中: {t.count(tok)}")
        # 摘要/方法首屏
        idx = t.find("Abstract")
        seg = t[idx : idx + 2600] if idx > 0 else t[:2600]
        buf.append("    ...")
        for line in seg.split("\n"):
            line = line.strip()
            if line:
                buf.append("    " + line[:280])

    OUT.write_text("\n".join(buf), encoding="utf-8")
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
