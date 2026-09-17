#!/usr/bin/env python3
"""Archive 《成人乙型肝炎疫苗接种专家建议》(2024) as a PDF.

The publisher hides the PDF button behind a JS handler and headless printing of
the live page returns a placeholder, so the article HTML is fetched, cleaned,
rebuilt locally and printed — the same strategy used for CDC Figure 2.4.
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
URL = "https://www.lcgdbzz.com/article/doi/10.12449/JCH240808"
OUT_NAME = "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)
    print(msg)


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "ignore")


TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
BLOCK_RE = re.compile(r"<(p|h1|h2|h3|h4|li|tr|div|br|table|td|th)[^>]*>", re.I)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)


def strip_tags(frag: str) -> str:
    frag = re.sub(r"<br\s*/?>", "\n", frag, flags=re.I)
    frag = re.sub(r"<[^>]+>", "", frag)
    return html.unescape(frag).strip()


def to_html(frag: str) -> str:
    """Convert an article fragment into readable HTML (tables preserved)."""
    out: list[str] = []
    pos = 0
    for m in ROW_RE.finditer(frag):
        if m.start() > pos:
            out.append(text_block(frag[pos : m.start()]))
        cells = [f"<td>{html.escape(strip_tags(c))}</td>" for c in CELL_RE.findall(m.group(1))]
        out.append("<table><tr>" + "".join(cells) + "</tr></table>")
        pos = m.end()
    out.append(text_block(frag[pos:]))
    return "\n".join(x for x in out if x)


def text_block(frag: str) -> str:
    parts = re.split(r"</?(?:p|h1|h2|h3|h4|li|div)[^>]*>", frag, flags=re.I)
    lines = [html.escape(strip_tags(p)) for p in parts]
    lines = [l for l in lines if l]
    return "".join(f"<p>{l}</p>" for l in lines)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    raw = fetch()
    raw = TAG_RE.sub("", raw)

    # main article body: everything that is not navigation/footer
    body = ""
    for pat in (
        r'<div[^>]*class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>\s*</div>',
        r'<div[^>]*class="[^"]*articleCon[^"]*"[^>]*>(.*?)</div>\s*</div>',
        r'<div[^>]*id="articleContent"[^>]*>(.*?)</div>\s*</div>',
    ):
        m = re.search(pat, raw, re.S | re.I)
        if m:
            body = m.group(1)
            break
    if len(body) < 2000:
        # fall back: take the longest <div> run, which is usually the article
        cands = re.findall(r"<div[^>]*>(.*?)</div>", raw, re.S | re.I)
        body = max(cands, key=len) if cands else raw
    log(f"raw={len(raw)} body={len(body)}")

    inner = to_html(body)
    page = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>成人乙型肝炎疫苗接种专家建议（2024）</title>
<style>
 body{{font-family:"Microsoft YaHei","SimSun",Arial,sans-serif;margin:26px;
       color:#111;line-height:1.65;font-size:13px}}
 h1{{font-size:19px;margin:0 0 6px;text-align:center}}
 h2{{font-size:14px;font-weight:400;color:#555;margin:0 0 6px;text-align:center}}
 .meta{{font-size:12px;color:#444;margin:0 0 16px;text-align:center;
        border-bottom:1px solid #ccc;padding-bottom:10px}}
 p{{margin:0 0 8px;text-indent:0}}
 table{{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}}
 td{{border:1px solid #bbb;padding:4px 6px}}
 .src{{margin-top:18px;font-size:11.5px;color:#333;border-top:1px solid #ccc;
       padding-top:10px;line-height:1.6}}
</style></head><body>
<h1>成人乙型肝炎疫苗接种专家建议</h1>
<h2>Expert recommendations on hepatitis B vaccination in adults</h2>
<div class="meta">中华预防医学会促进消除病毒性肝炎工作委员会，
中华预防医学会感染性疾病防控分会<br>
临床肝胆病杂志, 2024, 40(8): 1551-1556. DOI: 10.12449/JCH240808<br>
（同步发表于：中国病毒病杂志, 2024, 14(4): 310-316）</div>
{inner}
<div class="src">
来源：{URL}<br>
本文件为官网全文页的结构化存档（下载日期 2026-09-15）。因出版商 PDF 下载入口为
JavaScript 占位链接、无头浏览器直接打印返回占位内容，故按官网 HTML 全文重建后打印；
文字内容以出版商正式版为准。
</div></body></html>"""

    local = ROOT / "scripts" / "_rec_html_tmp.html"
    local.write_text(page, encoding="utf-8")
    log(f"rebuilt html {len(page)} chars")

    out = DEST / OUT_NAME
    profile = Path(tempfile.mkdtemp(prefix="_edgeprofile_", dir=ROOT / "scripts"))
    cmd = [
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
    ]
    try:
        subprocess.run(
            cmd, timeout=180, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    finally:
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
    local.unlink(missing_ok=True)
    if out.exists() and out.stat().st_size > 20000:
        log(f"OK {out.stat().st_size / 1024:.0f} KB -> {out.name}")
    else:
        size = out.stat().st_size if out.exists() else 0
        log(f"FAIL size={size}")
        if out.exists():
            out.unlink()
    (ROOT / "scripts" / "_rec_archive_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
