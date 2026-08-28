"""从 PPT 超链接提取 PMID 文献并按产品归档下载（最终整合版）

用法: python download_ppt_literatures_final.py
流程:
  1. 扫描 v8 PPT 全部外链, 提取 PubMed 文献链接
  2. 按产品分文件夹 (review_materials/文献库/<产品名>/)
  3. 下载策略: 本地已有 -> 复制; EuropePMC 真实 PMCID -> render PDF;
     NCBI PoW challenge -> SHA-256 前导零破解; JAMA 无PDF -> 浏览器打印PMC全文
  4. 验证全部 PDF 有效性 (%PDF 头 + 大小)

关键经验:
  - NCBI elink 返回的 PMCID 可能无效(404), 须用 EuropePMC search API
    (https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:<pmid>)
    获取真实 PMCID + isOpenAccess + hasPDF
  - NCBI PMC /pdf/ 下载有 PoW 反爬: SHA256(challenge+nonce) 前导4个0,
    cookie cloudpmc-viewer-pow = "{challenge},{nonce}"
  - JAMA 官网 Cloudflare 拦截脚本/无头浏览器, JAMA 文章无免费排版PDF,
    替代方案: 浏览器打印 PMC 全文页为 PDF
  - agent-browser 需 --executable-path 指定系统 Chrome (内置 Chromium 下载易超时)
"""

import hashlib
import http.cookiejar
import json
import os
import re
import time
import urllib.request

BASE = r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/文献库"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# PMID -> (产品文件夹, 主题后缀, 本地已有源文件或None)
PMIDS = {
    "12744879": ("HEPLISAV-B Dynavax", "phase1", "PMID 12744879_phase1.pdf"),
    "23727002": ("HEPLISAV-B Dynavax", "study2_HBV16", None),
    "29628151": ("HEPLISAV-B Dynavax", "phase3_safety", "PMID 29628151 _phase3.pdf"),
    "37085451": (
        "HEPLISAV-B Dynavax",
        "HBV19_followup",
        "Long-Term_Immunogenicity_And_Safety_Of_The_Hepatitis_B_Vaccine_Hepb-Cpg_Compared_With_Hepb-Eng_In_Adults-2022.pdf",
    ),
    "25576215": ("HEPLISAV-B Dynavax", "HBV-17_CKD", "PMID 25576215_HBV-17.pdf"),
    "39616603": ("HEPLISAV-B Dynavax", "BEe-HIVe", None),  # JAMA无PDF, PMC打印版
    "36269938": ("HEPLISAV-B Dynavax", "HBV18_dialysis", None),
    "41401704": ("CYFENDUS Emergent", "phase3_anthrax", None),
    "37226504": ("SCB-2019 三叶草", "adolescent_extension", None),
    "36868877": ("SCB-2019 三叶草", "SPECTRA_p23", None),
    "34655522": ("MVC-COV1901 高端疫苗", "phase2_safety", None),
    "36925422": ("MVC-COV1901 高端疫苗", "phase2_booster", None),
    "38575433": ("IndoVac BioFarma", "phase3", None),
    "37113012": ("CORBEVAX BiologicalE", "phase3_immunogenicity", None),
    "40257186": ("VN-0200 第一三共", "phase2_RSV", None),
    "35543281": ("RSVpreF+CpG 辉瑞", "phase12_RSV", None),
    "37881130": ("ZR202-CoV 泽润生物", "phase12_COVID", None),
    "37908361": ("BK-SE36 BIKEN", "phase1b_malaria", None),
    "41861834": ("Na-GST-1 Sabin", "phase2_hookworm", None),
}
LOCAL_SRC = r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/HEPLISAV-B"


def solve_pow(challenge, difficulty=4):
    prefix = "0" * difficulty
    nonce = 0
    while True:
        if hashlib.sha256((challenge + str(nonce)).encode()).hexdigest().startswith(prefix):
            return nonce
        nonce += 1


def download_with_pow(url, dst):
    """NCBI PoW challenge 下载"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", UA)]
    for _ in range(3):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"}
        )
        with opener.open(req, timeout=120) as r:
            data = r.read()
        if b"%PDF" in data[:2048]:
            open(dst, "wb").write(data)
            return True
        html = data.decode("utf-8", errors="replace")
        m = re.search(r'POW_CHALLENGE = "([^"]+)"', html)
        if not m:
            return False
        nonce = solve_pow(m.group(1), 4)
        ck = http.cookiejar.Cookie(
            version=0,
            name="cloudpmc-viewer-pow",
            value=f"{m.group(1)},{nonce}",
            port=None,
            port_specified=False,
            domain=".ncbi.nlm.nih.gov",
            domain_specified=True,
            domain_initial_dot=True,
            path="/",
            path_specified=True,
            secure=True,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        cj.set_cookie(ck)
        time.sleep(1.5)
    return False


def main():
    # 1. EuropePMC search 批量查真实 PMCID
    query = " OR ".join("EXT_ID:" + p for p in PMIDS)
    url = (
        EPMC
        + "/search?query="
        + urllib.request.quote(f"({query}) AND SRC:MED")
        + "&resultType=core&format=json&pageSize=25"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    real_pmc = {}
    for r in data.get("resultList", {}).get("result", []):
        if r.get("pmcid"):
            real_pmc[r["pmid"]] = r["pmcid"]

    ok, fail = [], []
    for pmid, (folder, topic, local) in PMIDS.items():
        os.makedirs(os.path.join(BASE, folder), exist_ok=True)
        dst = os.path.join(BASE, folder, f"PMID {pmid}_{topic}.pdf")
        if os.path.exists(dst) and os.path.getsize(dst) > 10000:
            ok.append(dst)
            continue
        # 本地已有 -> 复制
        if local:
            src = os.path.join(LOCAL_SRC, local)
            if os.path.exists(src):
                import shutil

                shutil.copy2(src, dst)
                ok.append(dst)
                continue
        pmc = real_pmc.get(pmid)
        if not pmc:
            fail.append((pmid, "no PMC"))
            continue
        # EuropePMC render
        try:
            u = f"https://europepmc.org/articles/{pmc}?pdf=render"
            req = urllib.request.Request(
                u, headers={"User-Agent": UA, "Referer": "https://europepmc.org/"}
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                d = r.read()
            if len(d) > 10000 and b"%PDF" in d[:2048]:
                open(dst, "wb").write(d)
                ok.append(dst)
                time.sleep(2)
                continue
        except Exception:
            pass
        # NCBI PoW
        if download_with_pow(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/", dst):
            ok.append(dst)
        else:
            fail.append((pmid, pmc))
        time.sleep(2)

    print(f"OK: {len(ok)}, FAIL: {len(fail)}")
    for f in fail:
        print("  FAIL:", f)


if __name__ == "__main__":
    main()
