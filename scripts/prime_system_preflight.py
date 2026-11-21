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
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = "ops/prime_system_integration_matrix.json"
EVIDENCE_LEVELS = {
    "SOURCE_INSPECTED_ONLY",
    "FOCUSED_CI_TESTED",
    "SQLITE_INTEGRATION_TESTED",
    "POSTGRES_INTEGRATION_TESTED",
    "STAGING_VERIFIED",
    "LIVE_OPERATION_VERIFIED",
}
ALLOWED_PRIORITIES = {"P0", "P1", "P2"}
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
    try:
        doc = json.loads(matrix_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "issues": [f"invalid matrix: {type(exc).__name__}"], "capability_count": 0}

    rows = doc.get("capabilities")
    if not isinstance(rows, list) or len(rows) < 20:
        return {"ok": False, "issues": ["expected at least 20 structured capabilities"], "capability_count": 0}

    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    known = set(ids)
    if len(known) != len(rows):
        issues.append("duplicate or missing capability identifiers")

    for row in rows:
        if not isinstance(row, dict):
            issues.append("capability entry must be a mapping")
            continue
        identifier = str(row.get("id"))
        missing = sorted(MANDATORY_KEYS - row.keys())
        if missing:
            issues.append(f"{identifier}: missing keys {missing}")
            continue
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
