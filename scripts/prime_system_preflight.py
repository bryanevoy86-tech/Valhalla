#!/usr/bin/env python3
"""Read-only, token-free Prime capability contract preflight.

This script DOES NOT certify runtime integrations, vendors, financial events,
workers, AI accuracy, or customer acquisition. It validates source-code
traceability and prevents evidence-stage inflation in the capability matrix.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = "ops/prime_system_integration_matrix.json"
HANDOFF_PATH = "docs/CODEX_RESUME_2026-12-01.md"
EVIDENCE_LEVELS = {
    "SOURCE_INSPECTED_ONLY",
    "FOCUSED_CI_TESTED",
    "SQLITE_INTEGRATION_TESTED",
    "POSTGRES_INTEGRATION_TESTED",
    "STAGING_VERIFIED",
    "LIVE_OPERATION_VERIFIED",
}
ALLOWED_PRIORITIES = {"P0", "P1", "P2"}
REMAINING_WORK_CLASSES = (
    "internal_coding",
    "internally_achievable_testing",
    "external_api_and_provider_commissioning",
    "owner_authorization_or_account_establishment",
    "independent_financial_or_operational_evidence",
    "qualified_professional_review",
    "conditional_future_expansion",
)
JANUARY_LAUNCH_FIELDS = {
    "implemented_and_tested", "january_core", "first_one_time_cad", "first_recurring_cad",
    "other_initial_legacies", "after_launch", "external_commissioning", "owner_or_professional",
    "launch_acceptance_evidence", "next_action",
}
MANDATORY_KEYS = {
    "id",
    "priority",
    "source_paths",
    "source_observation",
    "evidence_level",
    "production_verified",
    "acceptance_test",
    "depends_on",
    "owner_external_authorization_required",
}


def inspect_matrix(root: Path = REPO_ROOT, matrix_path: str = MATRIX_PATH) -> dict[str, Any]:
    root = root.resolve()
    matrix_file = root / matrix_path
    issues: list[str] = []
    examined_files = set()
    remaining_counts = dict.fromkeys(REMAINING_WORK_CLASSES, 0)
    p0_coding_count = 0
    classified = []
    try:
        doc = json.loads(matrix_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "issues": [f"invalid matrix: {type(exc).__name__}"], "capability_count": 0}

    rows = doc.get("capabilities")
    if not isinstance(rows, list) or len(rows) != 50:
        return {"ok": False, "issues": ["expected 50 structured capabilities"],
                "capability_count": len(rows) if isinstance(rows, list) else 0}

    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    known = set(ids)
    if len(known) != len(rows):
        issues.append("duplicate or missing capability identifiers")

    task_count = 0
    try:
        register = (root / HANDOFF_PATH).read_text(encoding="utf-8").split(
            "## Reconstructed task register and later workstreams", 1,
        )[1].split("### Safely retrieve current work", 1)[0]
        task_rows = re.findall(r"^\| (\d{2}) \| ([^|]+) \|", register, flags=re.MULTILINE)
        task_count = len(task_rows)
        mappings = [entry.split("`")[1] for _, entry in task_rows[3:] if entry.startswith("`")]
        if [number for number, _ in task_rows] != [f"{number:02}" for number in range(1, 54)] or mappings != ids:
            issues.append("December handoff must map all 53 tasks in order to the acceptance inventory")
    except (OSError, UnicodeError, IndexError):
        issues.append("December handoff task register unavailable")

    for row in rows:
        if not isinstance(row, dict):
            issues.append("capability entry must be a mapping")
            continue
        identifier = str(row.get("id"))
        missing = sorted(MANDATORY_KEYS - row.keys())
        if missing:
            issues.append(f"{identifier}: missing keys {missing}")
            continue
        continuation = row.get("continuation")
        work = continuation.get("remaining") if isinstance(continuation, dict) else None
        if not isinstance(work, dict) or work.keys() != set(REMAINING_WORK_CLASSES):
            issues.append(f"{identifier}: expected all seven separate remaining-work classes")
        else:
            for kind, note in work.items():
                if note is not None:
                    if not isinstance(note, str) or not note.strip():
                        issues.append(f"{identifier}: {kind} must be a nonempty note or null")
                    else:
                        remaining_counts[kind] += 1
            by_category = {
                "internally_implementable": ("internal_coding", "internally_achievable_testing"),
                "staging_or_independent_evidence": ("owner_authorization_or_account_establishment",
                                                    "independent_financial_or_operational_evidence"),
                "external_provider_dependent": ("external_api_and_provider_commissioning",),
                "professionally_gated": ("qualified_professional_review",),
                "future_capability": ("conditional_future_expansion",),
            }
            classified.append({
                "id": identifier, "priority": row["priority"], "evidence_level": row["evidence_level"],
                "outstanding": {category: {key: work[key] for key in keys if work[key] is not None}
                                for category, keys in by_category.items() if any(work[key] is not None for key in keys)},
            })
            if row["priority"] == "P0" and isinstance(work["internal_coding"], str) and work["internal_coding"].strip():
                p0_coding_count += 1
                gates = continuation.get("january_2027_launch_gates")
                if (not isinstance(gates, dict) or gates.keys() != JANUARY_LAUNCH_FIELDS
                        or any(not isinstance(value, str) or not value.strip() for value in gates.values())):
                    issues.append(f"{identifier}: every January launch gate requires explicit evidence and scope")
        if row["priority"] not in ALLOWED_PRIORITIES:
            issues.append(f"{identifier}: invalid priority")
        if row["evidence_level"] not in EVIDENCE_LEVELS:
            issues.append(f"{identifier}: invalid evidence level")
        if not isinstance(row["production_verified"], bool):
            issues.append(f"{identifier}: production_verified must be boolean")
        if not isinstance(row["owner_external_authorization_required"], bool):
            issues.append(f"{identifier}: external authorization flag must be boolean")
        if row["production_verified"]:
            if row.get("evidence_level") != "LIVE_OPERATION_VERIFIED":
                issues.append(f"{identifier}: unsupported live claim")
            for proof in ("live_receipt", "deployed_commit", "live_test_timestamp"):
                if not row.get(proof):
                    issues.append(f"{identifier}: unsupported production VERIFIED, missing {proof}")
        if not row["source_observation"] or not row["acceptance_test"]:
            issues.append(f"{identifier}: observation or acceptance contract empty")
        paths = row["source_paths"]
        if not isinstance(paths, list) or not paths:
            issues.append(f"{identifier}: no source files")
            continue
        for raw_path in paths:
            if not isinstance(raw_path, str):
                issues.append(f"{identifier}: invalid path data")
                continue
            candidate = (root / raw_path).resolve(strict=False)
            if not candidate.is_relative_to(root):
                issues.append(f"{identifier}: source path escapes repository")
                continue
            if not candidate.is_file():
                issues.append(f"{identifier}: missing source {raw_path}")
                continue
            examined_files.add(raw_path)
            if candidate.suffix == ".py":
                try:
                    ast.parse(candidate.read_text(encoding="utf-8-sig"), filename=raw_path)
                except (SyntaxError, UnicodeError) as exc:
                    issues.append(f"{identifier}: Python syntax unavailable in {raw_path}: {type(exc).__name__}")
        for dep in row.get("depends_on", []):
            if dep not in known:
                issues.append(f"{identifier}: unknown dependency {dep}")

    return {
        "ok": not issues,
        "capability_count": len(rows),
        "source_file_count": len(examined_files),
        "task_count": task_count,
        "capability_gap_classification": classified,
        "remaining_work_counts": remaining_counts,
        "p0_internal_coding_count": p0_coding_count,
        "issues": issues,
        "warning": (
            "Source inspection only. This cannot prove route registration, "
            "Postgres concurrency, vendor operations, real sales or revenue."
        ),
        "production_verified_count": sum(
            row.get("production_verified", False) is True for row in rows if isinstance(row, dict)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable report")
    parser.add_argument("--root", default=str(REPO_ROOT))
    args = parser.parse_args()
    result = inspect_matrix(Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Prime preflight: {result['capability_count']} domains, "
              f"{result.get('source_file_count', 0)} source anchors, "
              f"{len(result['issues'])} static issues.")
        for issue in result["issues"]:
            print("BLOCKER:", issue)
        print(result.get("warning", ""))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
