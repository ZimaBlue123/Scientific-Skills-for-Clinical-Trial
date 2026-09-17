"""提取 Heyward 2013 (HBV-16) 摘要与方法/结果中关于 n 与各时间点 SPR 的原文。"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

LIB = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials"
    r"\文献库-F2F Meeting"
)
OUT = Path(__file__).with_name("_heyward16_abstract.txt")
PDFS = [
    LIB
    / (
        "02_同类产品-CpG佐剂与对照疫苗/HEPLISAV-B Dynavax/"
        "Immunogenicity_and_Safety_of_Investigational_HBV_Vaccine_with_TLR9_Agonist_in_Healthy_Adults-2013.pdf"
    ),
]
OK = re.compile(r"\d{3}\.\d|\bn\s*=|randomized|enrolled|week 28|SPR|participants", re.I)


def main() -> None:
    buf: list[str] = []
    for p in PDFS:
        hits = [p] if p.exists() else list(LIB.rglob(p.name))
        for f in hits:
            buf.append(f"=== {f}")
            t = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(f)).pages)
            i = t.find("a b s t r a c t")
            if i < 0:
                i = t.find("abstract")
            seg = t[i : i + 4200]
            for line in seg.split("\n"):
                s = re.sub(r"\s+", " ", line).strip()
                if s:
                    buf.append("  " + s)
            buf.append("")
            buf.append("---- 全文中含 '1123' / '94.8' / '72.8' / '90.0' 的片段 ----")
            for tok in ("1123", "359", "94.8", "72.8", "90.0", "70.5"):
                for m in re.finditer(re.escape(tok), t):
                    s = max(0, m.start() - 160)
                    frag = re.sub(r"\s+", " ", t[s : m.end() + 160])
                    buf.append(f"  [{tok}] ...{frag}...")
    OUT.write_text("\n".join(buf), encoding="utf-8")
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
