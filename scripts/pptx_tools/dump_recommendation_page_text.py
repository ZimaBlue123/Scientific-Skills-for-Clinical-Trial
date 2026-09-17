"""Dump the plain text of the 2024 adult HepB vaccination recommendation page.

Used to (a) confirm the exact wording quoted on slide 8 and (b) rebuild a clean
archive PDF whose body is the recommendations (not the reference list).
"""

from __future__ import annotations

import html
import re
import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
OUT = ROOT / "scripts" / "_rec_page_text.txt"
URL = "https://www.lcgdbzz.com/article/doi/10.12449/JCH240808"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

req = urllib.request.Request(URL, headers={"User-Agent": UA})
with urllib.request.urlopen(req, timeout=90) as r:
    raw = r.read().decode("utf-8", "ignore")

raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)

# keep the region between the article title banner and the reference list
start = raw.find("成人乙型肝炎疫苗接种专家建议")
end = raw.find("参考文献")
seg = raw[start if start > 0 else 0 : end if end > 0 else len(raw)]

seg = re.sub(r"<br\s*/?>", "\n", seg, flags=re.I)
seg = re.sub(r"</(p|div|h1|h2|h3|li|tr)>", "\n", seg, flags=re.I)
seg = re.sub(r"<[^>]+>", "", seg)
text = html.unescape(seg)
text = re.sub(r"[ \t\xa0]+", " ", text)
text = re.sub(r"\n{3,}", "\n\n", text).strip()

OUT.write_text(text, encoding="utf-8")
