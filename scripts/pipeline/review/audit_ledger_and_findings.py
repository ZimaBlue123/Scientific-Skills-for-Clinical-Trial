"""Clinical audit coverage ledger, three-state findings schema, and report renderer.

Adapts multi-phase audit discipline (deterministic coverage ledger, adversarial
candidate disproof, three-state machine-readable verdicts, and target-neutral
reporting) for retrospective clinical trial reviews (CSR, DSUR, DRR, Protocol).

Public API
----------
- ``init_coverage_ledger``
- ``validate_coverage_ledger``
- ``summarize_coverage``
- ``validate_findings``
- ``render_audit_markdown``
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
VALID_UNIT_CATEGORIES = (
    "section",
    "table",
    "listing",
    "figure",
    "endpoint",
    "appendix",
)
VALID_UNIT_STATUSES = ("pending", "checked", "changed", "na")
VALID_VERDICTS = ("confirmed", "needs_validation", "rejected")
VALID_SEVERITIES = ("P0", "P1", "P2", "P3")
_SEVERITY_RANK = {sev: idx for idx, sev in enumerate(VALID_SEVERITIES)}


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def init_coverage_ledger(
    study_id: str,
    document: str,
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a normalized coverage ledger dictionary for a clinical audit."""
    if not _is_nonempty_str(study_id):
        raise ValueError("study_id must be a non-empty string")
    if not _is_nonempty_str(document):
        raise ValueError("document must be a non-empty string")
    if not units:
        raise ValueError("units must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    for raw in units:
        normalized.append(
            {
                "unit_id": str(raw.get("unit_id", "")).strip(),
                "title": str(raw.get("title", "")).strip(),
                "category": str(raw.get("category", "section")).strip(),
                "status": str(raw.get("status", "pending")).strip(),
                "notes": str(raw.get("notes", "")).strip(),
            }
        )

    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id.strip(),
        "document": document.strip(),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "units": normalized,
    }
    errors = validate_coverage_ledger(ledger, require_complete=False)
    if errors:
        raise ValueError("; ".join(errors))
    return ledger


def _validate_unit(
    unit: Any,
    idx: int,
    seen_ids: set[str],
    require_complete: bool,
) -> list[str]:
    if not isinstance(unit, dict):
        return [f"units[{idx}] must be an object"]

    errors: list[str] = []
    uid = unit.get("unit_id")
    if not _is_nonempty_str(uid):
        errors.append(f"units[{idx}].unit_id must be a non-empty string")
    elif uid in seen_ids:
        errors.append(f"duplicate unit_id: {uid!r}")
    else:
        seen_ids.add(uid)

    if not _is_nonempty_str(unit.get("title")):
        errors.append(f"units[{idx}].title must be a non-empty string")
    if unit.get("category") not in VALID_UNIT_CATEGORIES:
        errors.append(f"units[{idx}].category invalid: {unit.get('category')!r}")

    status = unit.get("status")
    if status not in VALID_UNIT_STATUSES:
        errors.append(f"units[{idx}].status invalid: {status!r}")
    elif require_complete and status in ("pending", "changed"):
        errors.append(f"units[{idx}] ({uid}) is incomplete: status={status!r}")
    return errors


def validate_coverage_ledger(
    ledger: dict[str, Any],
    require_complete: bool = False,
) -> list[str]:
    """Validate coverage ledger schema and optionally enforce 100% completion."""
    if not isinstance(ledger, dict):
        return ["ledger must be a JSON object"]

    errors: list[str] = []
    if ledger.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if not _is_nonempty_str(ledger.get("study_id")):
        errors.append("study_id must be a non-empty string")
    if not _is_nonempty_str(ledger.get("document")):
        errors.append("document must be a non-empty string")

    units = ledger.get("units")
    if not isinstance(units, list) or not units:
        errors.append("units must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for idx, unit in enumerate(units):
        errors.extend(_validate_unit(unit, idx, seen_ids, require_complete))
    return errors


def summarize_coverage(ledger: dict[str, Any]) -> dict[str, Any]:
    """Return status counts and completion flag for a validated ledger."""
    counts = {status: 0 for status in VALID_UNIT_STATUSES}
    units = ledger.get("units", [])
    for unit in units:
        st = unit.get("status")
        if st in counts:
            counts[st] += 1
    total = len(units)
    complete = total > 0 and counts["pending"] == 0 and counts["changed"] == 0
    return {"total": total, "counts": counts, "complete": complete}


def _validate_confirmed_fields(
    item: dict[str, Any],
    prefix: str,
    require_verified: bool,
) -> list[str]:
    errors: list[str] = []
    for field in ("source_ref", "observed_evidence", "recommendation"):
        if not _is_nonempty_str(item.get(field)):
            errors.append(f"{prefix}.{field} is required for confirmed verdict")
    if item.get("severity") not in VALID_SEVERITIES:
        errors.append(f"{prefix}.severity must be one of {VALID_SEVERITIES}")
    if _is_nonempty_str(item.get("unresolved_fact")):
        errors.append(f"{prefix}.unresolved_fact must be empty for confirmed verdict")
    if require_verified and item.get("independent_verified") is not True:
        errors.append(f"{prefix}.independent_verified must be true when verified gate is active")
    return errors


def _validate_verdict_fields(
    item: dict[str, Any],
    prefix: str,
    require_verified: bool,
) -> list[str]:
    verdict = item.get("verdict")
    if verdict == "confirmed":
        return _validate_confirmed_fields(item, prefix, require_verified)

    errors: list[str] = []
    if item.get("severity") is not None:
        errors.append(f"{prefix}.severity must be omitted/null for {verdict!r} verdict")

    if verdict == "needs_validation":
        if not _is_nonempty_str(item.get("source_ref")):
            errors.append(f"{prefix}.source_ref is required for needs_validation")
        if not _is_nonempty_str(item.get("unresolved_fact")):
            errors.append(f"{prefix}.unresolved_fact is required for needs_validation")
    elif verdict == "rejected":
        if not _is_nonempty_str(item.get("disproof_reason")):
            errors.append(f"{prefix}.disproof_reason is required for rejected verdict")
    return errors


def _validate_single_finding(
    item: Any,
    idx: int,
    seen_ids: set[str],
    unit_ids: set[str] | None,
    require_verified: bool,
) -> list[str]:
    prefix = f"findings[{idx}]"
    if not isinstance(item, dict):
        return [f"{prefix} must be an object"]

    errors: list[str] = []
    fid = item.get("finding_id")
    if not _is_nonempty_str(fid):
        errors.append(f"{prefix}.finding_id must be a non-empty string")
    elif fid in seen_ids:
        errors.append(f"duplicate finding_id: {fid!r}")
    else:
        seen_ids.add(fid)

    for req in ("unit_id", "dimension", "title"):
        if not _is_nonempty_str(item.get(req)):
            errors.append(f"{prefix}.{req} must be a non-empty string")

    if unit_ids is not None and item.get("unit_id") not in unit_ids:
        errors.append(f"{prefix}.unit_id {item.get('unit_id')!r} not in coverage ledger")

    if item.get("verdict") not in VALID_VERDICTS:
        errors.append(f"{prefix}.verdict must be one of {VALID_VERDICTS}")
        return errors

    errors.extend(_validate_verdict_fields(item, prefix, require_verified))
    return errors


def validate_findings(
    payload: dict[str, Any],
    ledger: dict[str, Any] | None = None,
    require_verified: bool = False,
) -> list[str]:
    """Validate three-state findings JSON against schema and optional ledger."""
    if not isinstance(payload, dict):
        return ["findings payload must be a JSON object"]

    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if not _is_nonempty_str(payload.get("study_id")):
        errors.append("study_id must be a non-empty string")

    unit_ids: set[str] | None = None
    if ledger is not None:
        ledger_errs = validate_coverage_ledger(ledger, require_complete=False)
        if ledger_errs:
            errors.extend(f"ledger: {err}" for err in ledger_errs)
        else:
            unit_ids = {u["unit_id"] for u in ledger["units"]}
            if payload.get("study_id") != ledger.get("study_id"):
                errors.append("study_id mismatch between findings and coverage ledger")

    items = payload.get("findings")
    if not isinstance(items, list):
        errors.append("findings must be a list")
        return errors

    seen_ids: set[str] = set()
    for idx, item in enumerate(items):
        errors.extend(_validate_single_finding(item, idx, seen_ids, unit_ids, require_verified))
    return errors


def _format_coverage_block(ledger: dict[str, Any]) -> list[str]:
    summary = summarize_coverage(ledger)
    counts = summary["counts"]
    lines = [
        "## Coverage Summary",
        "",
        "| Document | Total Units | Checked | Pending | Changed | N/A | Complete |",
        "|---|---:|---:|---:|---:|---:|:---:|",
        f"| {ledger['document']} | {summary['total']} | {counts['checked']} "
        f"| {counts['pending']} | {counts['changed']} | {counts['na']} "
        f"| {'Yes' if summary['complete'] else 'No'} |",
        "",
    ]
    return lines


def _format_confirmed_section(confirmed: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(
        confirmed,
        key=lambda x: (_SEVERITY_RANK.get(x["severity"], 99), x["finding_id"]),
    )
    lines = ["## Confirmed Findings", ""]
    if not ordered:
        lines.extend(["No confirmed findings.", ""])
        return lines

    lines.extend(
        [
            "| ID | Severity | Unit | Dimension | Title | Source Ref |",
            "|---|:---:|---|---|---|---|",
        ]
    )
    for item in ordered:
        lines.append(
            f"| {item['finding_id']} | {item['severity']} | {item['unit_id']} "
            f"| {item['dimension']} | {item['title']} | {item['source_ref']} |"
        )
    lines.append("")
    for item in ordered:
        lines.extend(
            [
                f"### {item['finding_id']} [{item['severity']}] {item['title']}",
                f"- **Unit / Dimension**: `{item['unit_id']}` / {item['dimension']}",
                f"- **Source Ref**: {item['source_ref']}",
                f"- **Observed Evidence**: {item['observed_evidence']}",
                f"- **Recommendation**: {item['recommendation']}",
                "",
            ]
        )
    return lines


def render_audit_markdown(
    payload: dict[str, Any],
    ledger: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Render target-neutral ``(REPORT.md, NEEDS-VALIDATION.md)`` from validated data."""
    errors = validate_findings(payload, ledger=ledger, require_verified=False)
    if errors:
        raise ValueError("Invalid findings payload: " + "; ".join(errors))

    items: list[dict[str, Any]] = payload["findings"]
    confirmed = [x for x in items if x["verdict"] == "confirmed"]
    needs_val = [x for x in items if x["verdict"] == "needs_validation"]
    rejected = [x for x in items if x["verdict"] == "rejected"]

    report_lines = [
        f"# Clinical Audit Report — {payload['study_id']}",
        "",
        f"- **Schema Version**: `{SCHEMA_VERSION}`",
        f"- **Confirmed**: {len(confirmed)} | **Needs Validation**: {len(needs_val)} "
        f"| **Rejected (Disproved)**: {len(rejected)}",
        "",
    ]
    if ledger is not None:
        report_lines.extend(_format_coverage_block(ledger))
    report_lines.extend(_format_confirmed_section(confirmed))

    nv_lines = [
        f"# Needs Validation Checklist — {payload['study_id']}",
        "",
    ]
    if not needs_val:
        nv_lines.extend(["No pending clarification items.", ""])
    else:
        nv_lines.extend(
            [
                "| ID | Unit | Dimension | Source Ref | Unresolved Fact |",
                "|---|---|---|---|---|",
            ]
        )
        for item in needs_val:
            nv_lines.append(
                f"| {item['finding_id']} | {item['unit_id']} | {item['dimension']} "
                f"| {item['source_ref']} | {item['unresolved_fact']} |"
            )
        nv_lines.append("")

    return "\n".join(report_lines), "\n".join(nv_lines)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-ledger", help="Initialize a coverage ledger JSON")
    p_init.add_argument("--study-id", required=True)
    p_init.add_argument("--document", required=True)
    p_init.add_argument("--units-json", required=True, help="JSON list of audit unit objects")
    p_init.add_argument("-o", "--output", required=True)

    p_vl = sub.add_parser("validate-ledger", help="Validate coverage-ledger.json")
    p_vl.add_argument("ledger")
    p_vl.add_argument("--require-complete", action="store_true")

    p_vf = sub.add_parser("validate-findings", help="Validate findings.json")
    p_vf.add_argument("findings")
    p_vf.add_argument("--ledger", default=None)
    p_vf.add_argument("--require-verified", action="store_true")

    p_ren = sub.add_parser("render-reports", help="Render REPORT.md and NEEDS-VALIDATION.md")
    p_ren.add_argument("findings")
    p_ren.add_argument("--ledger", default=None)
    p_ren.add_argument("--out-dir", required=True)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "init-ledger":
            units = _load_json(Path(args.units_json))
            ledger = init_coverage_ledger(args.study_id, args.document, units)
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"OK: wrote ledger ({len(ledger['units'])} units) -> {out}")
            return 0

        if args.command == "validate-ledger":
            ledger = _load_json(Path(args.ledger))
            errors = validate_coverage_ledger(ledger, require_complete=args.require_complete)
            if errors:
                for err in errors:
                    print(f"ERROR: {err}", file=sys.stderr)
                return 1
            summary = summarize_coverage(ledger)
            print(f"PASS: ledger valid (total={summary['total']}, complete={summary['complete']})")
            return 0

        if args.command == "validate-findings":
            payload = _load_json(Path(args.findings))
            ledger = _load_json(Path(args.ledger)) if args.ledger else None
            errors = validate_findings(
                payload, ledger=ledger, require_verified=args.require_verified
            )
            if errors:
                for err in errors:
                    print(f"ERROR: {err}", file=sys.stderr)
                return 1
            print(f"PASS: findings valid ({len(payload['findings'])} records)")
            return 0

        payload = _load_json(Path(args.findings))
        ledger = _load_json(Path(args.ledger)) if args.ledger else None
        report_md, nv_md = render_audit_markdown(payload, ledger=ledger)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "REPORT.md").write_text(report_md, encoding="utf-8")
        (out_dir / "NEEDS-VALIDATION.md").write_text(nv_md, encoding="utf-8")
        print(f"OK: rendered REPORT.md and NEEDS-VALIDATION.md -> {out_dir}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
