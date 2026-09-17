#!/usr/bin/env python3
"""Download / archive the references cited on slides 7 and 8 of the EOP2 deck.

Chinese journal sites render full text as HTML (no public PDF), so headless Edge
print-to-PDF is used to produce a faithful archive copy.

Usage:
    python download_slide7_8_references.py
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

JOBS = [
    # (target filename, url, needs_wait_seconds)
    (
        "蒋伟2022_中国大陆居民2004-2017年乙肝发病趋势_中国公共卫生-38(3)-257-261.pdf",
        "https://www.zgggws.com/article/doi/10.11847/zgggws1132715",
        12,
    ),
    (
        "中华预防医学会2024_成人乙型肝炎疫苗接种专家建议_临床肝胆病杂志-40(8)-1551-1556.pdf",
        "https://www.lcgdbzz.com/article/doi/10.12449/JCH240808",
        12,
    ),
    (
        "CDC_2023_Hepatitis-Surveillance_Figure2-4_Acute-HepB-Rates-by-Age.pdf",
        "https://www.cdc.gov/hepatitis-surveillance-2023/hepatitis-b/figure-2-4.html",
        15,
    ),
]

_log: list[str] = []


def log(msg: str) -> None:
    _log.append(msg)
    print(msg)


def print_to_pdf(url: str, out: Path, wait: int) -> bool:
    profile = Path(tempfile.mkdtemp(prefix="_edgeprofile_", dir=ROOT / "scripts"))
    cmd = [
        EDGE,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={profile}",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--virtual-time-budget={wait * 1000}",
        f"--print-to-pdf={out}",
        url,
    ]
    try:
        subprocess.run(
            cmd, timeout=180, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as exc:  # noqa: BLE001
        log(f"  ERROR edge: {exc}")
        return False
    finally:
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
    return out.exists() and out.stat().st_size > 20000


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    for name, url, wait in JOBS:
        out = DEST / name
        log(f"--- {name}")
        log(f"    url: {url}")
        ok = print_to_pdf(url, out, wait)
        if ok:
            log(f"    OK  {out.stat().st_size / 1024:.0f} KB")
        else:
            size = out.stat().st_size if out.exists() else 0
            log(f"    FAIL size={size}")
            if out.exists() and size <= 20000:
                out.unlink(missing_ok=True)
    (ROOT / "scripts" / "_slide7_8_download_log.txt").write_text("\n".join(_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
