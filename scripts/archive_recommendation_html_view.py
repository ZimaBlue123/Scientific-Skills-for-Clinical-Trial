"""Fetch the HTML full-text view of the 2024 adult HepB vaccination recommendation
and rebuild a clean archive PDF (body = recommendations, not the reference list).
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
OUT_NAME = "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

CANDIDATES = [
    "https://www.lcgdbzz.org/cn/article/doi/10.12449/JCH240808?viewType=HTML",
    "https://www.lcgdbzz.com/cn/article/doi/10.12449/JCH240808?viewType=HTML",
    "https://www.lcgdbzz.org/article/doi/10.12449/JCH240808?viewType=HTML",
]

_log: list[str] = []


def log(m: str) -> None:
    _log.append(m)
    print(m)


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")


def main() -> int:
    body = ""
    for url in CANDIDATES:
        try:
            raw = get(url)
        except Exception as exc:  # noqa: BLE001
            log(f"{url} -> ERROR {exc}")
            continue
        has_match = bool(re.search(r"18\s*[~～]\s*59", raw))
        log(f"{url} -> {len(raw)} bytes; has 18~59: {has_match}")
        if has_match:
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
            i = raw.find("成人乙型肝炎疫苗接种专家建议")
            j = raw.find("参考文献")
            body = raw[i if i > 0 else 0 : j if j > 0 else len(raw)]
            break

    if not body:
        log("NO full text found - keeping the previous metadata archive")
        (ROOT / "scripts" / "_rec_html2_log.txt").write_text("\n".join(_log), encoding="utf-8")
        return 0

    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</(p|div|h1|h2|h3|li|tr|table)>", "\n", body, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", body))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    log(f"body chars={len(text)}")
    log("--- preview ---")
    log(text[:1200])

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
<div class="src">来源：https://www.lcgdbzz.com/article/doi/10.12449/JCH240808<br>
本文件为官网 HTML 全文的结构化存档（下载日期 2026-09-15）。出版商 PDF 下载入口为
JavaScript 占位链接，无头浏览器直接打印返回占位内容，故按官网 HTML 全文重建后打印；
文字内容以出版商正式版为准。</div></body></html>"""

    local = ROOT / "scripts" / "_rec_html2_tmp.html"
    local.write_text(page, encoding="utf-8")
    out = DEST / OUT_NAME
    profile = Path(tempfile.mkdtemp(prefix="_edgeprofile_", dir=ROOT / "scripts"))
    try:
        subprocess.run(
            [
                EDGE,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                "--print-to-pdf-no-header",
                "--virtual-time-budget=8000",
                f"--print-to-pdf={out}",
                local.as_uri(),
            ],
            timeout=180,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
    local.unlink(missing_ok=True)
    log(f"PDF: {out.stat().st_size / 1024:.0f} KB" if out.exists() else "PDF FAIL")
    (ROOT / "scripts" / "_rec_html2_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
