"""
DSUR §13 Literature search:
- Search PubMed for safety-related varicella vaccine literature
- Window: 26-Jun-2025 to 25-Jun-2026
- Query terms match DSUR spec: "Varicella Vaccine" AND recombinant AND safety; AE; AR
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "DSUR-LitSearch/1.0"
OUTPUT_PATH = ".workbuddy/audit/pubmed_results.json"
DEFAULT_TIMEOUT = 30.0
RATE_LIMIT_SECONDS = 0.4

LOGGER = logging.getLogger("pubmed_lit_search")
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
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        LOGGER.error("HTTP failure for %s: %s", url, exc)
        raise
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        LOGGER.error("Malformed JSON from %s: %s", url, exc)
        raise


def esearch(term: str, mindate: str, maxdate: str, retmax: int = 20) -> dict[str, Any]:
    """Query NCBI esearch and return the parsed JSON envelope."""
    params = {
        "db": "pubmed",
        "term": term,
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",
        "retmax": retmax,
        "retmode": "json",
        "sort": "pub_date",
    }
    url = f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    return _http_get_json(url)


def esummary(pmids: list[str]) -> tuple[list[str], dict[str, Any]]:
    """Return (ordered uids, raw summary dict) for the given PMIDs."""
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
    """Build a normalized record for a single PMID."""
    rec = summary.get(uid, {}) if isinstance(summary, dict) else {}
    authors = rec.get("authors", []) or []
    first_author = authors[0].get("name", "") if authors else ""
    all_authors = ", ".join((a.get("name", "") for a in authors), )

    doi = ""
    pmcid = ""
    pii = ""
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
        "volume": rec.get("volume", ""),
        "issue": rec.get("issue", ""),
        "pages": rec.get("pages", ""),
        "doi": doi,
        "pmcid": pmcid,
        "pii": pii,
    }


def main() -> int:
    queries = [
        '"Varicella Vaccine"[tiab] AND recombinant[tiab] AND safety[tiab]',
        '"Varicella Vaccine"[tiab] AND "adverse event"[tiab]',
        '"Varicella Vaccine"[tiab] AND "adverse reaction"[tiab]',
        '"Varicella"[tiab] AND recombinant[tiab] AND safety[tiab]',
        '"VZV vaccine"[tiab] AND safety[tiab]',
        '"varicella vaccine"[tiab] AND "post-marketing"[tiab] AND safety[tiab]',
        '"varicella"[tiab] AND recombinant[tiab] AND immunogenicity[tiab]',
        '"herpes zoster vaccine"[tiab] AND recombinant[tiab] AND safety[tiab]',
        '"shingrix"[tiab] AND safety[tiab]',
    ]

    all_pmids: list[str] = []
    seen: set[str] = set()
    for q in queries:
        try:
            r = esearch(q, "2025/06/26", "2026/06/25", retmax=15)
            ids = r.get("esearchresult", {}).get("idlist", []) or []
            print(f"Q: {q}\n  hits: {len(ids)}  sample: {ids[:5]}")
            for pid in ids:
                if pid not in seen:
                    seen.add(pid)
                    all_pmids.append(pid)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            LOGGER.error("Query failed: %s  ERROR: %s", q, exc)
        time.sleep(RATE_LIMIT_SECONDS)

    print(f"\nTotal unique PMIDs: {len(all_pmids)}")
    try:
        uids, summary = esummary(all_pmids[:40])
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        LOGGER.error("esummary failed: %s", exc)
        return 1

    out = [_record_from_summary(uid, summary) for uid in uids]

    try:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        LOGGER.error("Cannot write %s: %s", OUTPUT_PATH, exc)
        return 1

    print(f"\nSaved {len(out)} records to {OUTPUT_PATH}")
    for r in out[:30]:
        print(f"PMID {r['pmid']} | {r['pubdate']} | {r['journal'][:30]} | {r['first_author']} | {r['title'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
