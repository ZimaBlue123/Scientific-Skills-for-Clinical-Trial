"""
HilleVax 诺如疫苗相关III期试验的PubMed文献检索。
- NCT06120764: HilleVax HIL-214 婴儿III期试验（约5个月大婴儿）
- NCT05507060: HilleVax HIL-214 成人III期试验（针对成人腹泻预防）
策略：
  1) 通过 ClinicalTrials.gov 数据集中 NCT ID 关联 PubMed 的 [si] 字段
  2) 同时使用关键词组合检索（HilleVax / HIL-214 / norovirus vaccine）作为补充
  3) 抓取摘要元数据并按试验分组
"""

import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "NorovirusTrialLitSearch/1.0"
DEFAULT_TIMEOUT = 30.0
RATE_LIMIT_SECONDS = 0.4

LOGGER = logging.getLogger("norovirus_trial_search")
if not LOGGER.handlers:
    _handler = logging.StreamHandler(stream=sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    LOGGER.addHandler(_handler)
    LOGGER.setLevel(logging.INFO)


def _http_get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Issue a GET against NCBI E-utilities and return parsed JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
    ) as exc:
        LOGGER.error("HTTP failure for %s: %s", url, exc)
        raise
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        LOGGER.error("Malformed JSON from %s: %s", url, exc)
        raise


def esearch(term: str, retmax: int = 50) -> list[str]:
    """Query NCBI esearch and return the PMID idlist."""
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "retmode": "json",
        "sort": "pub_date",
    }
    url = f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    data = _http_get_json(url)
    return data.get("esearchresult", {}).get("idlist", []) or []


def esummary(pmids: list[str]) -> dict[str, dict[str, Any]]:
    """Return {pmid: normalized_record} for the given PMIDs."""
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    url = f"{EUTILS}/esummary.fcgi?{urllib.parse.urlencode(params)}"
    data = _http_get_json(url)
    result = data.get("result", {}) or {}
    uids = result.get("uids", []) or []
    out: dict[str, dict[str, Any]] = {}
    for uid in uids:
        rec = result.get(uid, {}) or {}
        authors = rec.get("authors", []) or []
        first_author = authors[0].get("name", "") if authors else ""
        all_authors = "; ".join(a.get("name", "") for a in authors)

        doi = ""
        pmcid = ""
        for aid in rec.get("articleids", []) or []:
            t = aid.get("idtype", "")
            v = aid.get("value", "")
            if t == "doi":
                doi = v
            elif t == "pmc":
                pmcid = v

        out[uid] = {
            "pmid": uid,
            "title": rec.get("title", ""),
            "first_author": first_author,
            "authors": all_authors,
            "pubdate": rec.get("pubdate", ""),
            "journal": rec.get("source", "") or rec.get("fulljournalname", ""),
            "volume": rec.get("volume", ""),
            "issue": rec.get("issue", ""),
            "pages": rec.get("pages", ""),
            "doi": doi,
            "pmcid": pmcid,
        }
    return out


def search_for_trial(nct_id: str, label: str, extra_queries: list[str]) -> dict[str, Any]:
    """Collect PMIDs related to a single NCT trial."""
    print(f"\n=== {label} ({nct_id}) ===")
    seen: dict[str, str] = {}  # pmid -> query that found it

    # 1) 通过 NCT ID 字段直接关联
    direct_queries = [
        f"{nct_id}[si]",
        f"{nct_id}[Secondary Source ID]",
    ]
    # 2) 关键词补充
    keyword_queries = extra_queries

    all_queries = direct_queries + keyword_queries

    for q in all_queries:
        try:
            ids = esearch(q, retmax=50)
            print(f"  Q: {q}\n    hits: {len(ids)}  sample: {ids[:8]}")
            for pid in ids:
                if pid not in seen:
                    seen[pid] = q
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
        ) as exc:
            LOGGER.error("Query failed: %s  ERROR: %s", q, exc)
        time.sleep(RATE_LIMIT_SECONDS)

    pmids = list(seen.keys())
    print(f"  Total unique PMIDs: {len(pmids)}")

    summaries = {}
    if pmids:
        try:
            summaries = esummary(pmids)
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
        ) as exc:
            LOGGER.error("esummary failed: %s", exc)

    records = []
    for pid in pmids:
        rec = summaries.get(pid, {})
        rec["query_source"] = seen[pid]
        records.append(rec)

    # 按出版日期倒序
    records.sort(key=lambda r: r.get("pubdate", ""), reverse=True)
    return {"trial": nct_id, "label": label, "records": records, "count": len(records)}


def main() -> int:
    # NCT06120764: 婴儿 HIL-214 III期试验
    infant_queries = [
        "HilleVax[tiab] AND (infant*[tiab] OR pediatric[tiab])",
        '"HIL-214"[tiab]',
        "HilleVax[tiab] AND norovirus[tiab]",
        '"norovirus vaccine"[tiab] AND infant*[tiab] AND (phase III[tiab] OR phase 3[tiab])',
    ]

    # NCT05507060: 成人 HIL-214 III期试验
    adult_queries = [
        "HilleVax[tiab] AND adult*[tiab]",
        '"HIL-214"[tiab]',
        "HilleVax[tiab] AND norovirus[tiab]",
        '"norovirus vaccine"[tiab] AND adult*[tiab] AND (phase III[tiab] OR phase 3[tiab])',
    ]

    results = {
        "NCT06120764_infant": search_for_trial(
            "NCT06120764", "HilleVax 婴儿 III期试验 (HIL-214)", infant_queries
        ),
        "NCT05507060_adult": search_for_trial(
            "NCT05507060", "HilleVax 成人 III期试验 (HIL-214)", adult_queries
        ),
    }

    out_path = ".workbuddy/audit/norovirus_trial_pubmed.json"
    import os

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved -> {out_path}")

    # 控制台输出汇总
    for key, payload in results.items():
        print(f"\n--- {key} ({payload['count']} 条) ---")
        for r in payload["records"][:20]:
            print(f"  PMID {r.get('pmid')}: {r.get('title', '')[:120]}")
            print(
                f"    {r.get('first_author', '')} | {r.get('journal', '')} | {r.get('pubdate', '')}"
            )
            print(f"    DOI: {r.get('doi', '')} | via: {r.get('query_source', '')[:80]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
