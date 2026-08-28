"""
v6 链接真实性批量核验
=====================
1. ClinicalTrials.gov API 验证所有 NCT 号（存在性 + 官方标题）
2. PubMed eutils 验证所有 PMID（存在性 + 文献标题/期刊）
3. 其他域名 (FDA/WHO/ANZCTR/EATG/DOI/ChiCTR) 用 HTTP 状态检查
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation
from pptx.oxml.ns import qn

V6 = r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/60岁以上乙肝流调-CpG佐剂安全性-新佐剂减剂次临床意义-20260827-v6.pptx"


def collect_urls(pptx_path):
    """XML 级遍历所有 run 的 hlinkClick，收集去重 URL"""
    prs = Presentation(pptx_path)
    urls = set()
    for slide in prs.slides:
        part = slide.part
        for r_elem in slide._element.iter(qn("a:r")):
            rPr = r_elem.find(qn("a:rPr"))
            if rPr is None:
                continue
            hl = rPr.find(qn("a:hlinkClick"))
            if hl is None:
                continue
            rid = hl.get(qn("r:id"))
            if rid:
                try:
                    url = part.rels[rid].target_ref
                    if url.startswith("http"):
                        urls.add(url)
                except KeyError:
                    pass
    return urls


def http_ok(url, timeout=25):
    try:
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl()
    except Exception as e:
        return None, str(e)[:150]


def verify_nct(nct_list):
    """CT.gov API v2 批量查询"""
    results = {}
    for i in range(0, len(nct_list), 8):
        batch = nct_list[i : i + 8]
        url = (
            "https://clinicaltrials.gov/api/v2/studies?query.id=%s&format=json&pageSize=50"
            % urllib.parse.quote(",".join(batch))
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for study in data.get("studies", []):
                ps = study.get("protocolSection", {})
                idmod = ps.get("identificationModule", {})
                nct = idmod.get("nctId")
                title = idmod.get("officialTitle") or idmod.get("briefTitle")
                status = ps.get("statusModule", {}).get("overallStatus")
                phase = ps.get("designModule", {}).get("phases")
                results[nct] = {"title": title, "status": status, "phase": phase}
        except Exception as e:
            print("  CT.gov 批次查询失败: %s" % e)
        time.sleep(0.5)
    return results


def verify_pmid(pmid_list):
    """PubMed eutils esummary 批量查询"""
    results = {}
    ids = ",".join(pmid_list)
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=%s&retmode=json&tool=workbuddy&email=check@local"
        % ids
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for pmid, info in data.get("result", {}).items():
            if pmid == "uids":
                continue
            results[pmid] = {
                "title": info.get("title"),
                "journal": (info.get("fulljournalname") or info.get("source")),
                "pubdate": info.get("pubdate"),
            }
    except Exception as e:
        print("  PubMed 查询失败: %s" % e)
    return results


urls = collect_urls(V6)
print("去重 URL 总数:", len(urls))

# 按类型分组
ncts, pmids, others = set(), set(), set()
for u in urls:
    m = re.search(r"/study/(NCT\d{8})", u)
    if m:
        ncts.add(m.group(1))
        continue
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", u)
    if m:
        pmids.add(m.group(1))
        continue
    others.add(u)

print("\n===== 1) ClinicalTrials.gov NCT 号核验 (%d 个) =====" % len(ncts))
nct_ok = verify_nct(sorted(ncts))
for nct in sorted(ncts):
    info = nct_ok.get(nct)
    if info:
        print(
            "  ✅ %s | %s | %s | 期: %s"
            % (nct, (info["title"] or "")[:62], info["status"], info["phase"])
        )
    else:
        print("  ❌ %s | CT.gov 未找到!" % nct)

print("\n===== 2) PubMed PMID 核验 (%d 个) =====" % len(pmids))
pmid_ok = verify_pmid(sorted(pmids, key=int))
for pmid in sorted(pmids, key=int):
    info = pmid_ok.get(pmid)
    if info:
        print(
            "  ✅ %s | %s | %s | %s"
            % (pmid, (info["title"] or "")[:55], info["journal"], info["pubdate"])
        )
    else:
        print("  ❌ %s | PubMed 未找到!" % pmid)

print("\n===== 3) 其他链接 HTTP 状态检查 (%d 个) =====" % len(others))
for u in sorted(others):
    status, final = http_ok(u)
    if status:
        tag = "✅" if status < 400 else "⚠️"
        print("  %s %d | %s" % (tag, status, u[:95]))
    else:
        print("  ❌ | %s | %s" % (u[:95], final))
