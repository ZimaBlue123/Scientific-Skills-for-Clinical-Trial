#!/usr/bin/env python3
"""Build ClinicalTrials.gov registry-record PDFs via the CTG API v2.

The live study pages are JS-rendered and headless printing returns an empty
PDF, so the structured record is fetched from the official API, rendered as a
local HTML page, and printed to PDF with headless Edge.

Usage:
    python build_clinicaltrials_record_pdf.py
"""

from __future__ import annotations

import html
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")
DEST = (
    ROOT
    / "review_materials"
    / "文献库-F2F Meeting"
    / "02_同类产品-CpG佐剂与对照疫苗"
    / "HEPLISAV-B Dynavax"
    / "新增-细胞免疫补充（2026-09-15）"
)
TMP = ROOT / "scripts" / "_ctg_html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

STUDIES = [
    ("NCT04843852_BOOST-9_HEPLISAV-B_chronic-HBV_clinicaltrial-record.pdf", "NCT04843852"),
    ("NCT05727267_TherVacB_HEPLISAV-B-arm_clinicaltrial-record.pdf", "NCT05727267"),
]


def get_study(nct: str) -> dict:
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct}?format=json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)


def esc(x) -> str:
    return html.escape(str(x)) if x is not None else "—"


def walk_outcomes(mods, label):
    rows = []
    for m in mods or []:
        for o in m.get("outcomes") or []:
            rows.append((label, o.get("type", ""), o.get("measure", ""), o.get("timeFrame", "")))
    return rows


def build_html(data: dict, nct: str) -> str:
    p = data.get("protocolSection", {})
    idm = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    outcomes = p.get("outcomesModule", {})
    elig = p.get("eligibilityModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {})
    desc = p.get("descriptionModule", {})

    orows = []
    orows += walk_outcomes([{"outcomes": outcomes.get("primaryOutcomes")}], "主要")
    orows += walk_outcomes([{"outcomes": outcomes.get("secondaryOutcomes")}], "次要")
    orows += walk_outcomes([{"outcomes": outcomes.get("otherOutcomes")}], "其他")

    o_html = (
        "".join(
            f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>"
            for a, b, c, d in orows
        )
        or "<tr><td colspan='4'>未提供</td></tr>"
    )

    arm_html = (
        "".join(
            f"<li><b>{esc(a.get('label'))}</b>：{esc(a.get('description'))}"
            f"（类型：{esc(a.get('type'))}）</li>"
            for a in (arms.get("armGroups") or [])
        )
        or "<li>未提供</li>"
    )

    int_html = (
        "".join(
            f"<li>{esc(i.get('name'))}（{esc(i.get('type'))}）：{esc(i.get('description'))}</li>"
            for i in (arms.get("interventions") or [])
        )
        or "<li>未提供</li>"
    )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:28px;color:#222;
font-size:12px;line-height:1.6}}
h1{{font-size:20px;color:#A11C1D;border-bottom:2px solid #E3B8B8;
padding-bottom:6px}}
h2{{font-size:14px;color:#A11C1D;margin-top:18px}}
table{{border-collapse:collapse;width:100%;margin-top:6px}}
th,td{{border:1px solid #D9D9D9;padding:5px 7px;vertical-align:top;
font-size:11px}}
th{{background:#FBEAEA;text-align:left}}
.meta{{background:#FBEAEA;padding:8px 10px;margin:10px 0;font-size:11px}}
</style></head><body>
<h1>{esc(idm.get("briefTitle"))}</h1>
<div class="meta">
NCT 编号：{esc(nct)}　｜　官方标题：{esc(idm.get("officialTitle"))}<br>
申办/责任方：{esc((sponsor.get("leadSponsor") or {}).get("name"))}
　｜　合作者：{esc(", ".join(c.get("name", "") for c in (sponsor.get("collaborators") or [])) or "—")}<br>
研究状态：{esc(status.get("overallStatus"))}　｜　分期：{esc((design.get("phases") or ["—"])[0] if design.get("phases") else "—")}
　｜　入组：{esc((design.get("enrollmentInfo") or {}).get("count"))} 例<br>
开始：{esc((status.get("startDateStruct") or {}).get("date"))}
　｜　主要完成：{esc((status.get("primaryCompletionDateStruct") or {}).get("date"))}
　｜　研究完成：{esc((status.get("completionDateStruct") or {}).get("date"))}
</div>
<h2>简要摘要</h2><p>{esc(desc.get("briefSummary"))}</p>
<h2>详细说明</h2><p>{esc(desc.get("detailedDescription"))}</p>
<h2>研究分组</h2><ul>{arm_html}</ul>
<h2>干预措施</h2><ul>{int_html}</ul>
<h2>结局指标</h2><table>
<tr><th>类别</th><th>类型</th><th>指标</th><th>时间窗</th></tr>
{o_html}</table>
<h2>入选/排除要点</h2><p>最小年龄：{esc(elig.get("minimumAge"))}
　｜　最大年龄：{esc(elig.get("maximumAge"))}
　｜　健康志愿者：{esc(elig.get("healthyVolunteers"))}</p>
<p>{esc(elig.get("eligibilityCriteria"))}</p>
<hr><p style="font-size:10px;color:#666">
来源：ClinicalTrials.gov API v2（{esc(nct)}），下载日期 2026-09-15。
本文件为登记记录的结构化存档，非同行评议文献。</p>
</body></html>"""


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for filename, nct in STUDIES:
        dest = DEST / filename
        try:
            data = get_study(nct)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL {nct}: {exc}")
            continue
        html_path = TMP / f"{nct}.html"
        html_path.write_text(build_html(data, nct), encoding="utf-8")
        if dest.exists():
            dest.unlink()
        cmd = [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--user-data-dir={TMP / '_edgeprofile'}",
            f"--print-to-pdf={dest}",
            f"file:///{html_path.as_posix()}",
        ]
        subprocess.run(
            cmd, timeout=180, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ok = dest.exists() and dest.stat().st_size > 5000
        print(
            f"  {'OK  ' if ok else 'FAIL'} {filename} "
            f"({dest.stat().st_size // 1024 if ok else 0} KB)"
        )

    print("\n-- final contents --")
    for p in sorted(DEST.glob("*.pdf")):
        print(f"  {p.stat().st_size // 1024:>6} KB  {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
