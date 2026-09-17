#!/usr/bin/env python3
"""Archive the references cited on slides 7 and 8 of the EOP2 deck (p7/p8).

Three sources need different handling:

1. 蒋伟 2022 (中国公共卫生) — the magtech pattern
   /cn/article/pdf/preview/<doi>.pdf serves the publisher PDF directly.
2. CDC 2023 Hepatitis Surveillance, Figure 2.4 — the live page is JS-gated for
   headless printing, so the official data table is rendered locally and printed.
3. 《成人乙型肝炎疫苗接种专家建议》(2024, 临床肝胆病杂志) — the publisher PDF
   button is a JS placeholder and the body is loaded via AJAX, so the public
   metadata + article page HTML is rebuilt locally and printed.

Usage:
    python archive_slide7_8_references.py
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
DEST = ROOT / "review_materials" / "文献库-F2F Meeting" / "01_立题依据-流行病学与接种策略"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

JIANGWEI_PDF = "https://www.zgggws.com/cn/article/pdf/preview/10.11847/zgggws1132715.pdf"
JIANGWEI_OUT = "蒋伟2022_中国大陆居民2004-2017年乙肝发病趋势_中国公共卫生-38(3)-257-261.pdf"

CDC_OUT = "CDC_2023_Hepatitis-Surveillance_Figure2-4_Acute-HepB-Rates-by-Age.pdf"
CDC_URL = "https://www.cdc.gov/hepatitis-surveillance-2023/hepatitis-b/figure-2-4.html"

CDC26_OUT = "CDC_2023_Hepatitis-Surveillance_Table2-6_Chronic-HepB-Rates-by-Demographics.pdf"
CDC26_URL = "https://www.cdc.gov/hepatitis-surveillance-2023/hepatitis-b/table-2-6.html"
CDC26_XLSX = "https://www.cdc.gov/hepatitis-surveillance-2023/data/xlsx/table-2.6.xlsx"

REC_URL = "https://www.lcgdbzz.com/article/doi/10.12449/JCH240808"
REC_OUT = "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf"

CDC_YEARS = list(range(2008, 2024))
CDC_SERIES = {
    "0-19 years": [0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "20-29 years": [1.8, 1.2, 1.1, 1.0, 0.9, 0.8, 0.6, 0.8, 0.6, 0.6, 0.6, 0.5, 0.4, 0.4, 0.4, 0.5],
    "30-39 years": [2.7, 2.3, 2.3, 2.0, 2.2, 2.4, 2.2, 2.6, 2.4, 2.3, 2.0, 1.8, 1.0, 0.9, 0.7, 0.7],
    "40-49 years": [2.6, 2.2, 2.0, 1.9, 1.9, 2.1, 2.0, 2.4, 2.2, 2.5, 2.6, 2.7, 1.7, 1.6, 1.4, 1.4],
    "50-59 years": [1.5, 1.4, 1.5, 1.1, 1.1, 1.1, 1.2, 1.4, 1.5, 1.6, 1.6, 1.6, 1.2, 1.0, 1.2, 1.2],
    "≥60 years": [0.7, 0.7, 0.7, 0.5, 0.4, 0.4, 0.4, 0.5, 0.5, 0.6, 0.6, 0.6, 0.5, 0.5, 0.6, 0.7],
}

# CDC Table 2.6（2023 年新报告慢性乙肝病例数与率，按人口学特征）
# 结构：(分组, 特征, 病例数, 率/10万)
CDC26_SECTIONS: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "Age (years) 年龄组（岁）",
        [
            ("0–19", "248", "0.4"),
            ("20–29", "1,774", "4.7"),
            ("30–39", "3,965", "10.0"),
            ("40–49", "4,071", "11.4"),
            ("50–59", "3,418", "9.5"),
            ("≥60", "4,170", "5.9"),
        ],
    ),
    (
        "Sex 性别",
        [
            ("Male 男", "10,140", "7.1"),
            ("Female 女", "7,487", "5.1"),
        ],
    ),
    (
        "Race/ethnicity 种族/民族",
        [
            ("American Indian/Alaska Native, non-Hispanic", "48", "2.1"),
            ("Asian/Pacific Islander, non-Hispanic", "3,494", "18.9"),
            ("Black, non-Hispanic", "3,430", "9.5"),
            ("White, non-Hispanic", "3,279", "1.9"),
            ("Hispanic", "1,054", "2.0"),
            ("Other", "1,094", "n/a"),
        ],
    ),
    (
        "Urbanicity 城乡",
        [
            ("Urban 城市", "16,389", "6.5"),
            ("Rural 农村", "1,217", "3.2"),
        ],
    ),
]
CDC26_TOTAL = ("Total 合计", "17,650", "6.1")

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)
    print(msg)


def http_get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def print_to_pdf(target: str, out: Path, wait: int = 8) -> bool:
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
        log(f"  edge error: {exc}")
        return False
    finally:
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
    return out.exists() and out.stat().st_size > 20000


def build_cdc_html(path: Path) -> None:
    head = "".join(f"<th>{y}</th>" for y in CDC_YEARS)
    rows = "".join(
        f"<tr><th class='ag'>{age}</th>" + "".join(f"<td>{v:.1f}</td>" for v in vals) + "</tr>"
        for age, vals in CDC_SERIES.items()
    )
    path.write_text(
        f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>CDC 2023 Hepatitis Surveillance — Figure 2.4</title><style>
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
<p>来源：CDC. 2023 Hepatitis Surveillance Report — Figure 2.4.<br>{CDC_URL}<br>
数据下载：https://www.cdc.gov/hepatitis-surveillance-2023/data/xlsx/figure-2.4.xlsx</p>
<p><b>说明</b>：本文件为 CDC 官网公开数据表的结构化存档，因官网页面对无头浏览器打印
返回占位内容，故按官方数据表原值本地重建后打印。数值以 CDC 官网为准。</p>
</div></body></html>""",
        encoding="utf-8",
    )


def build_cdc_table26_html(path: Path) -> None:
    """按 CDC Table 2.6 官方数据表原值本地重建，供无头浏览器打印归档。"""
    body = (
        "<tr class='tot'><td colspan='3'>"
        f"{html.escape(CDC26_TOTAL[0])}</td>"
        f"<td class='n'>{CDC26_TOTAL[1]}</td>"
        f"<td class='n'>{CDC26_TOTAL[2]}</td></tr>"
    )
    for section, rows in CDC26_SECTIONS:
        body += f"<tr class='sec'><td colspan='5'>{html.escape(section)}</td></tr>"
        for name, n, rate in rows:
            body += (
                f"<tr><td></td><td colspan='2'>{html.escape(name)}</td>"
                f"<td class='n'>{n}</td><td class='n'>{rate}</td></tr>"
            )
    path.write_text(
        f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>CDC 2023 Hepatitis Surveillance — Table 2.6</title><style>
 body{{font-family:"Microsoft YaHei",Arial,sans-serif;margin:24px;color:#111}}
 h1{{font-size:19px;margin:0 0 4px}}
 h2{{font-size:14px;font-weight:400;color:#555;margin:0 0 14px}}
 table{{border-collapse:collapse;font-size:12.5px;width:100%}}
 th,td{{border:1px solid #bbb;padding:5px 8px}}
 th{{background:#f0f0f0;text-align:center}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums}}
 tr.tot td{{background:#f7f7f7;font-weight:700}}
 tr.sec td{{background:#eef3f8;font-weight:700}}
 .note{{margin-top:14px;font-size:12px;color:#444;line-height:1.6}}
 ul{{margin:8px 0 0 20px;padding:0}}
</style></head><body>
<h1>Table 2.6 — Chronic Hepatitis B: Case Rates by Demographics</h1>
<h2>Number and rate* of newly reported cases† of chronic hepatitis B, by
demographic characteristics — United States, 2023（率：每 10 万人口）</h2>
<table><thead><tr><th style="width:6%">&nbsp;</th>
<th colspan="2" style="width:58%">Characteristic 特征</th>
<th style="width:18%">No. 病例数</th><th style="width:18%">Rate* 率</th>
</tr></thead><tbody>{body}</tbody></table>
<div class="note">
<p><b>Key points</b>：2023 年新报告慢性乙型肝炎发病率在 30–39 岁、40–49 岁、
50–59 岁人群中最高。</p>
<ul>
<li>* 每 100,000 人口报告病例率；† 报告的确诊病例。</li>
<li>本表为第 7 页「美国（CDC 病毒性肝炎监测，2023）」慢性部分的直接来源；
与美国急性乙肝数据（Figure 2.4）相加后即为幻灯片所列合计值：
20–29 岁 4.7+0.5=5.2；30–39 岁 10.0+0.7=10.7；40–49 岁 11.4+1.4=12.8；
50–59 岁 9.5+1.2=10.7；≥60 岁 5.9+0.7=6.6。</li>
</ul>
<p>来源：CDC. 2023 Hepatitis Surveillance Report — Table 2.6.<br>{CDC26_URL}<br>
数据下载：{CDC26_XLSX}<br>
原始数据来源：CDC, National Notifiable Diseases Surveillance System.</p>
<p><b>说明</b>：本文件为 CDC 官网公开数据表的结构化存档，因官网页面对无头浏览器打印
返回占位内容，故按官方数据表原值本地重建后打印。数值以 CDC 官网为准。</p>
</div></body></html>""",
        encoding="utf-8",
    )


def archive_recommendation(out: Path) -> bool:
    raw = http_get(REC_URL).decode("utf-8", "ignore")
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
    i = raw.find("成人乙型肝炎疫苗接种专家建议")
    j = raw.find("参考文献")
    seg = raw[i if i > 0 else 0 : j if j > 0 else len(raw)]
    seg = re.sub(r"<br\s*/?>", "\n", seg, flags=re.I)
    seg = re.sub(r"</(p|div|h1|h2|h3|li|tr|table)>", "\n", seg, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", seg))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    paras = "".join(f"<p>{html.escape(p)}</p>" for p in text.split("\n") if p.strip())
    page = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>成人乙型肝炎疫苗接种专家建议（2024）</title><style>
 body{{font-family:"Microsoft YaHei","SimSun",Arial,sans-serif;margin:26px;
       color:#111;line-height:1.7;font-size:13px}}
 h1{{font-size:19px;margin:0 0 6px;text-align:center}}
 .meta{{font-size:12px;color:#444;margin:0 0 16px;text-align:center;
        border-bottom:1px solid #ccc;padding-bottom:10px}}
 p{{margin:0 0 9px}}
 .src{{margin-top:18px;font-size:11.5px;color:#333;border-top:1px solid #ccc;
       padding-top:10px;line-height:1.6}}
</style></head><body>
<h1>成人乙型肝炎疫苗接种专家建议</h1>
<div class="meta">中华预防医学会促进消除病毒性肝炎工作委员会；
中华预防医学会感染性疾病防控分会<br>
临床肝胆病杂志, 2024, 40(8): 1551-1556. DOI: 10.12449/JCH240808<br>
（同步发表于：中国病毒病杂志, 2024, 14(4): 310-316）</div>
{paras}
<div class="src">来源：{REC_URL}<br>
本文件为官网全文页的结构化存档。出版商 PDF 下载入口为 JavaScript 占位链接、
正文经 AJAX 加载，无头浏览器直接打印返回占位内容，故按官网公开内容重建后打印；
文字内容以出版商正式版为准（正式 PDF 722 KB，建议人工补存）。</div></body></html>"""
    local = ROOT / "scripts" / "_rec_rebuild_tmp.html"
    local.write_text(page, encoding="utf-8")
    ok = print_to_pdf(local.as_uri(), out)
    local.unlink(missing_ok=True)
    return ok


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    log("--- 1) 蒋伟 2022（中国公共卫生，出版社 PDF）")
    out = DEST / JIANGWEI_OUT
    try:
        data = http_get(JIANGWEI_PDF)
        if data[:5] == b"%PDF-" and len(data) > 50000:
            out.write_bytes(data)
            log(f"    OK {len(data) / 1024:.0f} KB")
        else:
            log(f"    FAIL not a PDF ({len(data)} bytes)")
    except Exception as exc:  # noqa: BLE001
        log(f"    ERROR {exc}")

    log("--- 2) CDC 2023 Figure 2.4（官方数据表重建）")
    out = DEST / CDC_OUT
    local = ROOT / "scripts" / "_cdc_fig24_tmp.html"
    build_cdc_html(local)
    ok = print_to_pdf(local.as_uri(), out)
    local.unlink(missing_ok=True)
    log(
        f"    {'OK' if ok else 'FAIL'} {out.stat().st_size / 1024:.0f} KB"
        if out.exists()
        else "    FAIL"
    )

    log("--- 3) CDC 2023 Table 2.6（慢性乙肝按人口学特征，官方数据表重建）")
    out = DEST / CDC26_OUT
    local = ROOT / "scripts" / "_cdc_tab26_tmp.html"
    build_cdc_table26_html(local)
    ok = print_to_pdf(local.as_uri(), out)
    local.unlink(missing_ok=True)
    log(
        f"    {'OK' if ok else 'FAIL'} {out.stat().st_size / 1024:.0f} KB"
        if out.exists()
        else "    FAIL"
    )

    log("--- 4) 成人乙型肝炎疫苗接种专家建议 2024（官网内容重建）")
    out = DEST / REC_OUT
    ok = archive_recommendation(out)
    log(
        f"    {'OK' if ok else 'FAIL'} {out.stat().st_size / 1024:.0f} KB"
        if out.exists()
        else "    FAIL"
    )

    (ROOT / "scripts" / "_archive_slide7_8_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
