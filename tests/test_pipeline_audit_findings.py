"""Unit tests for ``scripts/pipeline/review/audit_ledger_and_findings.py``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pipeline.review.audit_ledger_and_findings import (  # noqa: E402
    init_coverage_ledger,
    main,
    render_audit_markdown,
    summarize_coverage,
    validate_coverage_ledger,
    validate_findings,
)


def _sample_ledger(status: str = "checked") -> dict:
    return init_coverage_ledger(
        study_id="TVAX-020",
        document="DRR_V0.1.docx",
        units=[
            {"unit_id": "SEC-1", "title": "Study Overview", "category": "section", "status": status},
            {"unit_id": "TBL-2", "title": "AE Summary", "category": "table", "status": "checked"},
        ],
    )


def _sample_findings() -> dict:
    return {
        "schema_version": "1.0",
        "study_id": "TVAX-020",
        "findings": [
            {
                "finding_id": "F-002",
                "unit_id": "TBL-2",
                "dimension": "T1",
                "title": "Minor wording inconsistency",
                "verdict": "confirmed",
                "severity": "P2",
                "source_ref": "Table 2, p.14",
                "observed_evidence": "Header says N=120 while footnote says N=118",
                "recommendation": "Align footnote denominator to FAS N=120",
                "independent_verified": True,
            },
            {
                "finding_id": "F-001",
                "unit_id": "SEC-1",
                "dimension": "T0",
                "title": "SAE count mismatch vs EDC",
                "verdict": "confirmed",
                "severity": "P0",
                "source_ref": "Section 3.2, p.8",
                "observed_evidence": "Text reports 3 SAEs; EDC export lists 4 SAEs",
                "recommendation": "Update text count to 4 SAEs",
                "independent_verified": True,
            },
            {
                "finding_id": "F-003",
                "unit_id": "SEC-1",
                "dimension": "T4",
                "title": "Pending hospitalization discharge summary",
                "verdict": "needs_validation",
                "source_ref": "Subject 0102 SAE narrative",
                "unresolved_fact": "Exact discharge date missing from source PDF",
            },
            {
                "finding_id": "F-004",
                "unit_id": "TBL-2",
                "dimension": "T2",
                "title": "Apparent age discrepancy",
                "verdict": "rejected",
                "disproof_reason": "Protocol allows rounding at screening; EDC confirms 18y",
            },
        ],
    }


def test_ledger_init_validate_and_summary():
    ledger = _sample_ledger(status="pending")
    assert validate_coverage_ledger(ledger, require_complete=False) == []
    incomplete_errs = validate_coverage_ledger(ledger, require_complete=True)
    assert len(incomplete_errs) == 1
    assert "SEC-1" in incomplete_errs[0]
    summary = summarize_coverage(ledger)
    assert summary["total"] == 2
    assert summary["complete"] is False


def test_ledger_rejects_duplicate_unit_id():
    with pytest.raises(ValueError, match="duplicate unit_id"):
        init_coverage_ledger(
            study_id="TVAX-020",
            document="DRR.docx",
            units=[
                {"unit_id": "U1", "title": "A", "category": "section"},
                {"unit_id": "U1", "title": "B", "category": "table"},
            ],
        )


def test_validate_findings_valid_and_verified_gate():
    ledger = _sample_ledger()
    payload = _sample_findings()
    assert validate_findings(payload, ledger=ledger, require_verified=True) == []

    payload["findings"][0]["independent_verified"] = False
    errs = validate_findings(payload, ledger=ledger, require_verified=True)
    assert any("independent_verified" in e for e in errs)


def test_validate_findings_enforces_three_state_contracts():
    ledger = _sample_ledger()
    payload = _sample_findings()

    # needs_validation must NOT carry severity
    payload["findings"][2]["severity"] = "P1"
    # confirmed missing source_ref
    payload["findings"][0]["source_ref"] = ""
    # rejected missing disproof_reason
    payload["findings"][3]["disproof_reason"] = ""
    # unknown unit_id
    payload["findings"][1]["unit_id"] = "UNKNOWN-99"

    errs = validate_findings(payload, ledger=ledger)
    assert any("must be omitted/null" in e for e in errs)
    assert any("source_ref is required" in e for e in errs)
    assert any("disproof_reason is required" in e for e in errs)
    assert any("UNKNOWN-99" in e for e in errs)


def test_render_audit_markdown_orders_and_separates_states():
    ledger = _sample_ledger()
    payload = _sample_findings()
    report_md, nv_md = render_audit_markdown(payload, ledger=ledger)

    assert "| Confirmed | Needs Validation |" not in report_md
    assert "F-001" in report_md and "F-002" in report_md
    assert report_md.index("F-001") < report_md.index("F-002")
    assert "Apparent age discrepancy" not in report_md
    assert "F-003" in nv_md
    assert "Exact discharge date missing from source PDF" in nv_md
    assert "F-001" not in nv_md


def test_cli_roundtrip(tmp_path: Path):
    units_path = tmp_path / "units.json"
    ledger_path = tmp_path / "coverage-ledger.json"
    findings_path = tmp_path / "findings.json"
    out_dir = tmp_path / "out"

    units_path.write_text(
        json.dumps(
            [
                {"unit_id": "SEC-1", "title": "Overview", "category": "section", "status": "checked"},
                {"unit_id": "TBL-2", "title": "AE", "category": "table", "status": "checked"},
            ]
        ),
        encoding="utf-8",
    )
    assert (
        main(
            [
                "init-ledger",
                "--study-id",
                "TVAX-020",
                "--document",
                "DRR.docx",
                "--units-json",
                str(units_path),
                "-o",
                str(ledger_path),
            ]
        )
        == 0
    )
    assert main(["validate-ledger", str(ledger_path), "--require-complete"]) == 0

    findings_path.write_text(json.dumps(_sample_findings()), encoding="utf-8")
    assert (
        main(
            [
                "validate-findings",
                str(findings_path),
                "--ledger",
                str(ledger_path),
                "--require-verified",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "render-reports",
                str(findings_path),
                "--ledger",
                str(ledger_path),
                "--out-dir",
                str(out_dir),
            ]
        )
        == 0
    )
    assert (out_dir / "REPORT.md").is_file()
    assert (out_dir / "NEEDS-VALIDATION.md").is_file()
