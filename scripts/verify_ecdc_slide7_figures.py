"""核验第 7 页引用的 ECDC AER 2022 年龄组急性乙肝发病率数据。

幻灯片口头标注为：25–54 岁 6.3–9.7 / 10 万，55–64 岁 5.8 / 10 万，≥65 岁 3.7 / 10 万。
本脚本从库内 ECDC PDF 抽取全文，定位 Figure 4（按年龄/性别的急性乙肝报告率）
附近文本，输出年龄组与数值上下文，供人工核对。
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

PDF = (
    Path(__file__).resolve().parents[1]
    / "review_materials"
    / "文献库-F2F Meeting"
    / "01_立题依据-流行病学与接种策略"
    / "ECDC_Hepatitis-B-Annual-Epidemiological-Report-2022.pdf"
)
OUT = Path(__file__).with_name("_ecdc_slide7_verify.txt")

AGE_PAT = re.compile(r"(\d{2}\s*[–\-]\s*\d{2}|\d{2}\s*\+|≥\s*\d{2}|>\s*=\s*\d{2})", re.UNICODE)
RATE_PAT = re.compile(r"\b\d{1,3}\.\d{1,2}\b")


def main() -> None:
    lines: list[str] = []
    reader = PdfReader(str(PDF))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        try:
            pages.append((i, page.extract_text() or ""))
        except Exception as exc:  # noqa: BLE001
            pages.append((i, f"<extract failed: {exc}>"))

    lines.append(f"PDF: {PDF.name}")
    lines.append(f"Pages: {len(pages)}")
    lines.append("")

    # 1) 全文命中率：幻灯片上的三个数值
    full = "\n".join(t for _, t in pages)
    for token in ("6.3", "9.7", "5.8", "3.7"):
        lines.append(f"全文 '{token}' 命中次数: {full.count(token)}")
    lines.append("")

    # 2) 定位年龄组相关页
    hit_pages = []
    for i, text in pages:
        if re.search(r"[Aa]ge", text) and (
            "hepatitis B" in text.lower() or "HBV" in text or "acute" in text.lower()
        ):
            hit_pages.append(i)
    lines.append(f"疑似年龄组相关页: {hit_pages}")
    lines.append("")

    target = hit_pages[:6] if hit_pages else [i for i, _ in pages][:6]
    for i in target:
        text = pages[i - 1][1]
        if not text.strip():
            continue
        lines.append(f"===== Page {i} =====")
        lines.append(text.strip()[:2600])
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
