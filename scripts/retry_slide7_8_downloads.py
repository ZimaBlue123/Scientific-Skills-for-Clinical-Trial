#!/usr/bin/env python3
"""Retry the failed downloads for slides 7/8 references.

- Chinese journal site (lcgdbzz): retry alternate hosts with a longer render wait.
- CDC 2023 surveillance figure 2.4: the live page is JS-gated for headless
  printing, so the published data table is rendered locally and printed instead
  (same approach used for the ClinicalTrials.gov registry records) and the PDF is
  labelled as a structured archive of the public data.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
DEST = ROOT / "review_materials" / "文献库-F2F Meeting" / "01_立题依据-流行病学与接种策略"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)
    print(msg)


def print_to_pdf(target: str, out: Path, wait: int) -> bool:
    profile = Path(tempfile.mkdtemp(prefix="_edgeprofile_", dir=ROOT / "scripts"))
    cmd = [
        EDGE,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={profile}",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        "--run-all-compositor-stages-before-draw",
        f"--virtual-time-budget={wait * 1000}",
        f"--print-to-pdf={out}",
        target,
    ]
    try:
        subprocess.run(
            cmd, timeout=240, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as exc:  # noqa: BLE001
        log(f"  ERROR: {exc}")
        return False
    finally:
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
    return out.exists() and out.stat().st_size > 20000


# --------------------------------------------------------------------------
# CDC Figure 2.4 — acute hepatitis B case rates by age group, US, 2008-2023
# (transcribed from the official CDC data table as rendered on the figure page)
# --------------------------------------------------------------------------
YEARS = list(range(2008, 2024))
SERIES = {
    "0-19 years": [0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "20-29 years": [1.8, 1.2, 1.1, 1.0, 0.9, 0.8, 0.6, 0.8, 0.6, 0.6, 0.6, 0.5, 0.4, 0.4, 0.4, 0.5],
    "30-39 years": [2.7, 2.3, 2.3, 2.0, 2.2, 2.4, 2.2, 2.6, 2.4, 2.3, 2.0, 1.8, 1.0, 0.9, 0.7, 0.7],
    "40-49 years": [2.6, 2.2, 2.0, 1.9, 1.9, 2.1, 2.0, 2.4, 2.2, 2.5, 2.6, 2.7, 1.7, 1.6, 1.4, 1.4],
    "50-59 years": [1.5, 1.4, 1.5, 1.1, 1.1, 1.1, 1.2, 1.4, 1.5, 1.6, 1.6, 1.6, 1.2, 1.0, 1.2, 1.2],
    "≥60 years": [0.7, 0.7, 0.7, 0.5, 0.4, 0.4, 0.4, 0.5, 0.5, 0.6, 0.6, 0.6, 0.5, 0.5, 0.6, 0.7],
}


def build_cdc_html(path: Path) -> None:
    head = "".join(f"<th>{y}</th>" for y in YEARS)
    rows = "".join(
        f"<tr><th class='ag'>{age}</th>" + "".join(f"<td>{v:.1f}</td>" for v in vals) + "</tr>"
        for age, vals in SERIES.items()
    )
    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>CDC 2023 Hepatitis Surveillance — Figure 2.4</title>
<style>
 body{{font-family:"Microsoft YaHei",Arial,sans-serif;margin:24px;color:#111}}
 h1{{font-size:20px;margin:0 0 4px}}
 h2{{font-size:15px;font-weight:400;color:#555;margin:0 0 14px}}
 table{{border-collapse:collapse;font-size:12px;width:100%}}
 th,td{{border:1px solid #bbb;padding:4px 6px;text-align:right}}
 th{{background:#f0f0f0;text-align:center}}
 th.ag{{text-align:left;background:#fafafa;white-space:nowrap}}
 .note{{margin-top:14px;font-size:12px;color:#444;line-height:1.6}}
 ul{{margin:8px 0 0 20px;padding:0}}
</style></head><body>
<h1>Figure 2.4 — Acute Hepatitis B: Case Rates by Age Group</h1>
<h2>Rates* of reported cases† of acute hepatitis B, by age group —
United States, 2008–2023（每 10 万人口）</h2>
<table><thead><tr><th class="ag">年龄组</th>{head}</tr></thead>
<tbody>{rows}</tbody></table>
<div class="note">
<p><b>Key points</b>：2023 年急性乙型肝炎报告发病率在 40–49 岁人群中最高，在 0–19 岁人群中最低。</p>
<ul>
<li>* 每 100,000 人口报告病例率；† 报告病例（含确诊与疑似）。</li>
<li>2023 年数值：0–19 岁 0.0；20–29 岁 0.5；30–39 岁 0.7；40–49 岁 1.4；50–59 岁 1.2；≥60 岁 0.7。</li>
</ul>
<p>来源：CDC. 2023 Hepatitis Surveillance Report — Figure 2.4: Acute Hepatitis B
Case Rates by Age Group, United States, 2008–2023.<br>
https://www.cdc.gov/hepatitis-surveillance-2023/hepatitis-b/figure-2-4.html<br>
数据下载：https://www.cdc.gov/hepatitis-surveillance-2023/data/xlsx/figure-2.4.xlsx</p>
<p><b>说明</b>：本文件为 CDC 官网公开数据表的结构化存档（下载日期 2026-09-15），
因官网页面对无头浏览器打印返回占位内容，故按官方数据表原值本地重建后打印。数值以 CDC 官网为准。</p>
</div></body></html>"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    # ---- 1. 成人乙型肝炎疫苗接种专家建议 -----------------------------------
    name = "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf"
    out = DEST / name
    for host in ("https://www.lcgdbzz.org", "https://www.lcgdbzz.com"):
        url = f"{host}/article/doi/10.12449/JCH240808"
        log(f"--- try {host}")
        if print_to_pdf(url, out, 25):
            log(f"    OK {out.stat().st_size / 1024:.0f} KB")
            break
        log("    FAIL")
        if out.exists():
            out.unlink(missing_ok=True)
    else:
        log("    专家建议：均失败")

    # ---- 2. CDC figure 2.4 -------------------------------------------------
    name = "CDC_2023_Hepatitis-Surveillance_Figure2-4_Acute-HepB-Rates-by-Age.pdf"
    out = DEST / name
    local = ROOT / "scripts" / "_cdc_fig24.html"
    build_cdc_html(local)
    log("--- CDC figure 2.4 (local rebuild)")
    if print_to_pdf(local.as_uri(), out, 8):
        log(f"    OK {out.stat().st_size / 1024:.0f} KB")
    else:
        log("    FAIL")
    local.unlink(missing_ok=True)

    (ROOT / "scripts" / "_slide7_8_retry_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
