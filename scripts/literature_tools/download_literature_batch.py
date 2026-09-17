"""
Batch Literature PDF Downloader for F2F Meeting Library

Downloads open-access full-text PDFs for papers identified by PMID/DOI.
Tries multiple OA channels in sequence:
  1. Europe PMC (OA subset PDF)
  2. PubMed Central (PMC PDF via PMID→PMCID mapping)
  3. Unpaywall API (best OA PDF location)
  4. OpenAlex API (best_oa_location.pdf_url)
  5. Known OA publisher direct links (MDPI, Frontiers, PLoS, BMC, etc.)

Usage:
    python scripts/download_literature_batch.py [--dry-run]
"""

from __future__ import annotations

import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger("download_literature_batch")
if not LOGGER.handlers:
    _handler = logging.StreamHandler(stream=sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    LOGGER.addHandler(_handler)
    LOGGER.setLevel(logging.INFO)

USER_AGENT = "TVAX009-LitDownloader/1.0 (Clinical Trial Literature Review)"
UNPAYWALL_EMAIL = "literature-review@example.com"
DEFAULT_TIMEOUT = 30.0
RATE_LIMIT_DELAY = 0.5  # seconds between API requests

# Base path for the literature library
LIB_ROOT = Path(__file__).resolve().parent.parent / "review_materials" / "文献库-F2F Meeting"

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------


@dataclass
class LiteratureItem:
    """Represents one literature entry to download."""

    seq: int  # Sequence number from the missing list
    folder: str  # Target folder name (e.g., "01_立题依据-流行病学与接种策略")
    filename: str  # Target filename (e.g., "PMID 35260904_Hall2022_...")
    pmid: str = ""  # PubMed ID
    doi: str = ""  # DOI
    title_hint: str = ""  # Title keywords for fallback search
    status: str = "pending"  # pending / downloaded / failed
    fail_reason: str = ""  # Reason if failed
    source: str = ""  # Which channel succeeded
    file_size: int = 0  # Downloaded file size in bytes


# ---------------------------------------------------------------------------
# Literature Items — 19 entries with PMID/DOI
# ---------------------------------------------------------------------------

ITEMS: list[LiteratureItem] = [
    # --- 01 立题依据 (2) ---
    LiteratureItem(
        seq=7,
        folder="01_立题依据-流行病学与接种策略",
        filename="PMID 35260904_Hall2022_Cost-utility-universal-HepB-vaccination-adults-JInfectDis.pdf",
        pmid="35260904",
        doi="10.1093/infdis/jiac088",
        title_hint="Cost-utility universal hepatitis B vaccination adults",
    ),
    LiteratureItem(
        seq=8,
        folder="01_立题依据-流行病学与接种策略",
        filename="PMID 35358162_Weng2022_Universal-HepB-vaccination-adults-19-59-ACIP-MMWR71rr13.pdf",
        pmid="35358162",
        doi="10.15585/mmwr.mm7113a1",
        title_hint="Universal hepatitis B vaccination adults ACIP MMWR",
    ),
    # --- 02 同类产品 (3) ---
    LiteratureItem(
        seq=12,
        folder="02_同类产品-CpG佐剂与对照疫苗",
        filename="PMID 23727422_HBV17-CKD.pdf",
        pmid="23727422",
        doi="10.1016/j.vaccine.2013.05.067",
        title_hint="HBV-17 CKD HEPLISAV hepatitis B vaccine",
    ),
    LiteratureItem(
        seq=13,
        folder="02_同类产品-CpG佐剂与对照疫苗",
        filename="PMID 27718183_CpG-1018-case-study.pdf",
        pmid="27718183",
        doi="10.1007/978-1-4939-6445-1_2",
        title_hint="CpG adjuvant 1018 case study Methods Mol Biol",
    ),
    LiteratureItem(
        seq=14,
        folder="02_同类产品-CpG佐剂与对照疫苗",
        filename="PMID 21506647_CpG-DNA-vaccine-adjuvant.pdf",
        pmid="21506647",
        doi="10.1586/erv.10.174",
        title_hint="CpG DNA vaccine adjuvant Expert Rev Vaccines",
    ),
    # --- 03 免疫程序 (4) ---
    LiteratureItem(
        seq=15,
        folder="03_免疫程序-2针vs3针与依从性",
        filename="PMID 33252692_Bruxvoort2020_doses-completion-JAMANetwOpen.pdf",
        pmid="33252692",
        doi="10.1001/jamanetworkopen.2020.27577",
        title_hint="hepatitis B vaccine dose completion JAMA",
    ),
    LiteratureItem(
        seq=16,
        folder="03_免疫程序-2针vs3针与依从性",
        filename="PMID 26801063_WangZZ-2016-dosage-schedules.pdf",
        pmid="26801063",
        doi="10.1016/j.vaccine.2016.01.018",
        title_hint="Wang hepatitis B vaccine dosage schedules",
    ),
    LiteratureItem(
        seq=17,
        folder="03_免疫程序-2针vs3针与依从性",
        filename="PMID 29420134_WangZZ-2year-followup.pdf",
        pmid="29420134",
        doi="10.1080/21645515.2018.1438090",
        title_hint="Wang hepatitis B 2-year followup",
    ),
    LiteratureItem(
        seq=18,
        folder="03_免疫程序-2针vs3针与依从性",
        filename="PMID 36525511_Oelschlager-2023-2dose-vs-3dose.pdf",
        pmid="36525511",
        doi="10.1093/milmed/usac389",
        title_hint="2-dose vs 3-dose hepatitis B military",
    ),
    # --- 04 特殊人群 (10) ---
    LiteratureItem(
        seq=19,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 41479811_Singh_HBV-CKD-bench-to-bedside.pdf",
        pmid="41479811",
        doi="10.5527/wjn.v14.i4.109767",
        title_hint="hepatitis B CKD bench to bedside World J Nephrology",
    ),
    LiteratureItem(
        seq=22,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 36948364_Khalesi_HBV-hemodialysis-systematic-review.pdf",
        pmid="36948364",
        doi="10.1016/j.micpath.2023.106080",
        title_hint="hepatitis B hemodialysis systematic review",
    ),
    LiteratureItem(
        seq=26,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 23173138_Schillie_HepB-immune-response-diabetes-systematic-review.pdf",
        pmid="23173138",
        doi="10.2337/dc12-0312",
        title_hint="hepatitis B immune response diabetes systematic review",
    ),
    LiteratureItem(
        seq=28,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 30271742_Mavilia_HBV-HCV-coinfection.pdf",
        pmid="30271742",
        doi="10.14218/jcth.2018.00016",
        title_hint="HBV HCV coinfection",
    ),
    LiteratureItem(
        seq=29,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 35576953_Alberts_HBV-HCV-prevalence-cirrhosis.pdf",
        pmid="35576953",
        doi="10.1016/s2468-1253(22)00124-8",
        title_hint="hepatitis B C prevalence cirrhosis Lancet Gastroenterol",
    ),
    LiteratureItem(
        seq=31,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 8470423_Lefebure_HepB-vaccine-renal-transplant.pdf",
        pmid="8470423",
        doi="10.1016/0264-410x(93)90192-z",
        title_hint="hepatitis B vaccine renal transplant",
    ),
    LiteratureItem(
        seq=32,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 39460259_Hornung_Post-transplant-seroprotection-HepB.pdf",
        pmid="39460259",
        doi="10.3390/vaccines12101092",
        title_hint="post-transplant seroprotection hepatitis B Vaccines MDPI",
    ),
    LiteratureItem(
        seq=33,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 39793537_Chiu_HepB-CpG-thoracic-transplant.pdf",
        pmid="39793537",
        doi="10.1016/j.vaccine.2025.126705",
        title_hint="hepatitis B CpG thoracic transplant",
    ),
    LiteratureItem(
        seq=34,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 32716741_Hwang_HBV-screening-cancer-ASCO.pdf",
        pmid="32716741",
        doi="10.1200/jco.20.01757",
        title_hint="HBV screening cancer ASCO JCO",
    ),
    LiteratureItem(
        seq=35,
        folder="04_特殊人群-肾透析-糖尿病-低应答",
        filename="PMID 33259596_Pleyer_BTK-inhibitor-HepB-zoster-vaccines.pdf",
        pmid="33259596",
        doi="10.1182/blood.2020008758",
        title_hint="BTK inhibitor hepatitis B zoster vaccines Blood",
    ),
]


# ---------------------------------------------------------------------------
# HTTP Helpers
# ---------------------------------------------------------------------------


def _http_get(url: str, timeout: float = DEFAULT_TIMEOUT, accept: str = "") -> bytes | None:
    """GET request returning raw bytes, or None on failure."""
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as exc:
        LOGGER.debug("HTTP GET failed for %s: %s", url, exc)
        return None


def _http_get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any] | None:
    """GET request returning parsed JSON, or None on failure."""
    data = _http_get(url, timeout=timeout, accept="application/json")
    if data is None:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _is_valid_pdf(data: bytes) -> bool:
    """Check if data looks like a valid PDF (starts with %PDF)."""
    return data[:5] == b"%PDF-"


def _download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF from url to dest. Returns True if successful."""
    LOGGER.info("  Trying: %s", url)
    data = _http_get(url, timeout=60)
    if data is None:
        LOGGER.info("    -> Download failed (network error)")
        return False
    if len(data) < 1024:
        LOGGER.info("    -> Too small (%d bytes), likely error page", len(data))
        return False
    if not _is_valid_pdf(data):
        # Some servers return HTML error pages with 200 status
        LOGGER.info("    -> Not a valid PDF (wrong magic bytes)")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    LOGGER.info("    -> SUCCESS: %d bytes saved to %s", len(data), dest.name)
    return True


# ---------------------------------------------------------------------------
# OA Channel Functions
# ---------------------------------------------------------------------------


def try_europepmc_oa(item: LiteratureItem, dest: Path) -> bool:
    """Try Europe PMC OA REST API for full-text PDF."""
    if not item.pmid:
        return False
    # Europe PMC provides OA PDFs for PMC-indexed articles
    # First, get PMCID from Europe PMC
    search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{item.pmid}%20AND%20SRC:MED&format=json&resultType=core"
    result = _http_get_json(search_url)
    if result and result.get("resultList", {}).get("result"):
        article = result["resultList"]["result"][0]
        pmcid = article.get("pmcid", "")
        if pmcid:
            pdf_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"
            if _download_pdf(pdf_url, dest):
                return True
    return False


def try_pmc_pdf(item: LiteratureItem, dest: Path) -> bool:
    """Try downloading PDF directly from PubMed Central."""
    if not item.pmid:
        return False
    # Use NCBI ID converter to get PMCID
    converter_url = (
        f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={item.pmid}&format=json"
    )
    result = _http_get_json(converter_url)
    if result and result.get("records"):
        record = result["records"][0]
        pmcid = record.get("pmcid", "")
        if pmcid:
            # PMC PDF direct link
            pdf_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/"
            if _download_pdf(pdf_url, dest):
                return True
    return False


def try_unpaywall(item: LiteratureItem, dest: Path) -> bool:
    """Try Unpaywall API to find OA PDF URL."""
    if not item.doi:
        return False
    encoded_doi = urllib.parse.quote(item.doi, safe="")
    url = f"https://api.unpaywall.org/v2/{encoded_doi}?email={UNPAYWALL_EMAIL}"
    result = _http_get_json(url)
    if not result:
        return False

    # Try best_oa_location first, then all oa_locations
    locations = []
    best = result.get("best_oa_location")
    if best:
        locations.append(best)
    for loc in result.get("oa_locations", []):
        if loc not in locations:
            locations.append(loc)

    for loc in locations:
        pdf_url = loc.get("url_for_pdf") or loc.get("url")
        if pdf_url and pdf_url.endswith(".pdf") or pdf_url and loc.get("url_for_pdf"):
            if _download_pdf(pdf_url, dest):
                return True
    return False


def try_openalex(item: LiteratureItem, dest: Path) -> bool:
    """Try OpenAlex API to find OA PDF URL."""
    if not item.doi:
        return False
    doi_url = f"https://doi.org/{item.doi}"
    encoded = urllib.parse.quote(doi_url, safe="")
    url = f"https://api.openalex.org/works/{encoded}?mailto={UNPAYWALL_EMAIL}"
    result = _http_get_json(url)
    if not result:
        return False

    # Check best_oa_location
    best_oa = result.get("best_oa_location", {})
    if best_oa:
        pdf_url = best_oa.get("pdf_url")
        if pdf_url and _download_pdf(pdf_url, dest):
            return True

    # Check primary_location
    primary = result.get("primary_location", {})
    if primary:
        pdf_url = primary.get("pdf_url")
        if pdf_url and _download_pdf(pdf_url, dest):
            return True

    # Check all locations
    for loc in result.get("locations", []):
        pdf_url = loc.get("pdf_url")
        if pdf_url and _download_pdf(pdf_url, dest):
            return True
    return False


def try_doi_redirect(item: LiteratureItem, dest: Path) -> bool:
    """Try well-known OA publisher PDF patterns based on DOI."""
    if not item.doi:
        return False

    doi_lower = item.doi.lower()

    # MDPI (e.g., vaccines, sensors)
    if "10.3390/" in doi_lower:
        # Pattern: https://www.mdpi.com/{doi-suffix}/pdf
        # e.g., 10.3390/vaccines12101092 -> vaccines/12/10/1092
        parts = item.doi.split("/", 1)
        if len(parts) == 2:
            pdf_url = f"https://www.mdpi.com/{parts[1]}/pdf"
            if _download_pdf(pdf_url, dest):
                return True

    # Frontiers
    if "10.3389/" in doi_lower:
        pdf_url = f"https://www.frontiersin.org/articles/{item.doi}/pdf"
        if _download_pdf(pdf_url, dest):
            return True

    # PLoS
    if "10.1371/" in doi_lower:
        pdf_url = f"https://journals.plos.org/plosone/article/file?id={item.doi}&type=printable"
        if _download_pdf(pdf_url, dest):
            return True

    # CDC MMWR (public domain)
    if "10.15585/mmwr" in doi_lower:
        # Try CDC direct PDF
        pdf_url = "https://www.cdc.gov/mmwr/volumes/71/wr/pdfs/mm7113a1-H.pdf"
        if _download_pdf(pdf_url, dest):
            return True

    # World Journal of Nephrology (Baishideng, usually OA)
    if "10.5527/" in doi_lower:
        pdf_url = f"https://www.wjgnet.com/2220-6124/full/v14/i4/{item.doi.split('.')[-1]}.htm"
        # Baishideng doesn't have simple PDF patterns, skip
        pass

    # Journal of Clinical and Translational Hepatology
    if "10.14218/" in doi_lower:
        pdf_url = f"https://www.jcthnet.com/article/doi/{item.doi}"
        # Not a direct PDF link, skip
        pass

    # JAMA Network Open
    if "10.1001/jamanetworkopen" in doi_lower:
        pdf_url = (
            f"https://jamanetwork.com/journals/jamanetworkopen/articlepdf/{item.doi.split('.')[-1]}"
        )
        # JAMA doesn't have simple public PDF patterns
        pass

    return False


# ---------------------------------------------------------------------------
# Main Download Pipeline
# ---------------------------------------------------------------------------

CHANNELS = [
    ("Europe PMC", try_europepmc_oa),
    ("PMC PDF", try_pmc_pdf),
    ("Unpaywall", try_unpaywall),
    ("OpenAlex", try_openalex),
    ("DOI Direct", try_doi_redirect),
]


def download_one(item: LiteratureItem, dry_run: bool = False) -> None:
    """Attempt to download one literature item through all channels."""
    dest = LIB_ROOT / item.folder / item.filename
    if dest.exists():
        item.status = "downloaded"
        item.source = "already_exists"
        item.file_size = dest.stat().st_size
        LOGGER.info("[%02d] SKIP (already exists): %s", item.seq, item.filename)
        return

    LOGGER.info("[%02d] Downloading: %s", item.seq, item.filename)
    LOGGER.info("     PMID=%s  DOI=%s", item.pmid, item.doi)

    if dry_run:
        item.status = "dry_run"
        return

    for channel_name, channel_fn in CHANNELS:
        LOGGER.info("  Channel: %s", channel_name)
        try:
            success = channel_fn(item, dest)
        except Exception as exc:
            LOGGER.warning("  Channel %s error: %s", channel_name, exc)
            success = False

        if success:
            item.status = "downloaded"
            item.source = channel_name
            item.file_size = dest.stat().st_size
            return

        time.sleep(RATE_LIMIT_DELAY)

    item.status = "failed"
    item.fail_reason = "All OA channels exhausted (paywall or publisher restriction)"
    LOGGER.warning("[%02d] FAILED: %s", item.seq, item.filename)


def run_all(dry_run: bool = False) -> list[LiteratureItem]:
    """Download all items and return results."""
    LOGGER.info("=" * 72)
    LOGGER.info("Starting batch download: %d items", len(ITEMS))
    LOGGER.info("Library root: %s", LIB_ROOT)
    LOGGER.info("=" * 72)

    for item in ITEMS:
        download_one(item, dry_run=dry_run)
        time.sleep(RATE_LIMIT_DELAY)

    return ITEMS


def print_report(items: list[LiteratureItem]) -> None:
    """Print a summary report of download results."""
    downloaded = [i for i in items if i.status == "downloaded"]
    failed = [i for i in items if i.status == "failed"]
    skipped = [i for i in items if i.source == "already_exists"]

    print("\n" + "=" * 72)
    print("DOWNLOAD REPORT")
    print("=" * 72)
    print(f"Total items:    {len(items)}")
    print(
        f"Downloaded:     {len(downloaded)} (new: {len(downloaded) - len(skipped)}, existing: {len(skipped)})"
    )
    print(f"Failed:         {len(failed)}")
    print()

    if downloaded:
        print("--- Successfully Downloaded ---")
        for i in downloaded:
            size_kb = i.file_size / 1024
            print(f"  [{i.seq:02d}] {i.filename}")
            print(f"       Source: {i.source} | Size: {size_kb:.0f} KB")
        print()

    if failed:
        print("--- Failed (Paywall / Restricted) ---")
        for i in failed:
            print(f"  [{i.seq:02d}] {i.filename}")
            print(f"       PMID: {i.pmid} | DOI: {i.doi}")
            print(f"       Reason: {i.fail_reason}")
        print()


def save_report_json(items: list[LiteratureItem], path: Path) -> None:
    """Save structured report as JSON."""
    report = []
    for i in items:
        report.append(
            {
                "seq": i.seq,
                "folder": i.folder,
                "filename": i.filename,
                "pmid": i.pmid,
                "doi": i.doi,
                "status": i.status,
                "source": i.source,
                "file_size": i.file_size,
                "fail_reason": i.fail_reason,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info("Report saved to %s", path)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Batch Literature PDF Downloader")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List items without downloading",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="",
        help="Path to save JSON report (default: <lib_root>/download_report.json)",
    )
    args = parser.parse_args()

    items = run_all(dry_run=args.dry_run)
    print_report(items)

    report_path = Path(args.report) if args.report else LIB_ROOT / "download_report.json"
    save_report_json(items, report_path)

    failed_count = sum(1 for i in items if i.status == "failed")
    return 1 if failed_count == len(items) else 0


if __name__ == "__main__":
    sys.exit(main())
