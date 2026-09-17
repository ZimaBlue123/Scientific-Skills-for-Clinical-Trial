#!/usr/bin/env python3
"""Try the magtech '/cn/article/pdf/preview/<doi>.pdf' pattern for the journals
whose PDF button is JS-gated, and upgrade the already-printed 蒋伟2022 copy to
the publisher's real PDF when available.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
DEST = ROOT / "review_materials" / "文献库-F2F Meeting" / "01_立题依据-流行病学与接种策略"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

CANDIDATES = [
    # (output filename, candidate url)
    (
        "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf",
        "https://www.lcgdbzz.com/cn/article/pdf/preview/10.12449/JCH240808.pdf",
    ),
    (
        "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf",
        "https://www.lcgdbzz.org/cn/article/pdf/preview/10.12449/JCH240808.pdf",
    ),
    (
        "蒋伟2022_中国大陆居民2004-2017年乙肝发病趋势_中国公共卫生-38(3)-257-261.pdf",
        "https://www.zgggws.com/cn/article/pdf/preview/10.11847/zgggws1132715.pdf",
    ),
]

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)
    print(msg)


def looks_like_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-" and len(data) > 50000


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    for name, url in CANDIDATES:
        if name in done:
            continue
        out = DEST / name
        log(f"--- {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
        except Exception as exc:  # noqa: BLE001
            log(f"    ERROR {exc}")
            continue
        if looks_like_pdf(data):
            tmp = out.with_suffix(".tmp.pdf")
            tmp.write_bytes(data)
            tmp.replace(out)
            log(f"    OK {len(data) / 1024:.0f} KB -> {out.name}")
            done.add(name)
        else:
            log(f"    not a PDF (bytes={len(data)}, head={data[:20]!r})")
    (ROOT / "scripts" / "_direct_pdf_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
