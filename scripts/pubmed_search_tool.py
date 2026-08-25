"""
Unified PubMed Literature Search Tool

Consolidated from norovirus_trial_search.py and pubmed_lit_search.py.
Queries PubMed via NCBI E-utilities (esearch, esummary) to retrieve literature records.

Usage:
    python scripts/pubmed_search_tool.py --query '"Varicella Vaccine"[tiab] AND safety[tiab]' --mindate 2025/06/26 --maxdate 2026/06/25 --out result.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "DSUR-LitSearch/2.0"
DEFAULT_TIMEOUT = 30.0

LOGGER = logging.getLogger("pubmed_search_tool")
if not LOGGER.handlers:
    _handler = logging.StreamHandler(stream=sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    LOGGER.addHandler(_handler)
    LOGGER.setLevel(logging.INFO)


def _http_get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
    except Exception as exc:
        LOGGER.error("HTTP failure for %s: %s", url, exc)
        raise
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        LOGGER.error("Malformed JSON from %s: %s", url, exc)
        raise


def esearch(
    term: str, mindate: str = "", maxdate: str = "", retmax: int = 20
) -> dict[str, Any]:
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "retmode": "json",
        "sort": "pub_date",
    }
    if mindate:
        params["mindate"] = mindate
    if maxdate:
        params["maxdate"] = maxdate
    if mindate or maxdate:
        params["datetype"] = "pdat"

    url = f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    return _http_get_json(url)


def esummary(pmids: list[str]) -> tuple[list[str], dict[str, Any]]:
    if not pmids:
        return [], {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    url = f"{EUTILS}/esummary.fcgi?{urllib.parse.urlencode(params)}"
    data = _http_get_json(url)
    result = data.get("result", {})
    uids = result.get("uids", []) or []
    return uids, result


def _record_from_summary(uid: str, summary: dict[str, Any]) -> dict[str, Any]:
    rec = summary.get(uid, {}) if isinstance(summary, dict) else {}
    authors = rec.get("authors", []) or []
    first_author = authors[0].get("name", "") if authors else ""
    all_authors = ", ".join(a.get("name", "") for a in authors)

    doi = pmcid = pii = ""
    for aid in rec.get("articleids", []) or []:
        t = aid.get("idtype", "")
        v = aid.get("value", "")
        if t == "doi":
            doi = v
        elif t == "pmc":
            pmcid = v
        elif t == "pii":
            pii = v

    return {
        "pmid": uid,
        "title": rec.get("title", ""),
        "first_author": first_author,
        "authors": all_authors,
        "pubdate": rec.get("pubdate", ""),
        "journal": rec.get("source", "") or rec.get("fulljournalname", ""),
        "doi": doi,
        "pmcid": pmcid,
        "pii": pii,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified PubMed Search Tool")
    parser.add_argument("--query", type=str, required=True, help="PubMed search query")
    parser.add_argument(
        "--mindate", type=str, default="", help="Minimum publication date (YYYY/MM/DD)"
    )
    parser.add_argument(
        "--maxdate", type=str, default="", help="Maximum publication date (YYYY/MM/DD)"
    )
    parser.add_argument("--out", type=str, required=True, help="Output JSON path")
    parser.add_argument("--retmax", type=int, default=20, help="Max results to fetch")
    args = parser.parse_args()

    all_pmids: list[str] = []
    try:
        r = esearch(args.query, args.mindate, args.maxdate, retmax=args.retmax)
        ids = r.get("esearchresult", {}).get("idlist", []) or []
        print(f"Query: {args.query}\nHits: {len(ids)}")
        all_pmids.extend(ids)
    except Exception as exc:
        LOGGER.error("Query failed: %s", exc)
        return 1

    if not all_pmids:
        print("No results found.")
        return 0

    try:
        uids, summary = esummary(all_pmids)
    except Exception as exc:
        LOGGER.error("esummary failed: %s", exc)
        return 1

    out_records = [_record_from_summary(uid, summary) for uid in uids]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out_records, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(out_records)} records to {args.out}")
    for r in out_records[:10]:
        print(
            f"PMID {r['pmid']} | {r['pubdate']} | {r['first_author']} | {r['title'][:80]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
