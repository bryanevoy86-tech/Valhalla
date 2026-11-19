"""Conservative, evidence-backed go-live readiness checks.

A missing credential, provider confirmation, table, or runtime proof is a
failed check. Never mark a production capability ready using a hardcoded True.
"""
from __future__ import annotations

import importlib.util
import os


def _database_evidence() -> dict[str, bool]:
    evidence = {
        "database_connected": False,
        "schema_migrated": False,
        "contracts_templates_loaded": False,
        "audit_logging_enabled": False,
    }
    try:
        from sqlalchemy import inspect, text
        from app.core.db import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
            evidence["database_connected"] = True
            tables = set(inspect(conn).get_table_names())
            evidence["schema_migrated"] = "alembic_version" in tables
            evidence["audit_logging_enabled"] = "audit_log" in tables
            if "contract_templates" in tables:
                evidence["contracts_templates_loaded"] = (
                    conn.execute(text("SELECT 1 FROM contract_templates LIMIT 1")).first() is not None
                )
    except Exception:
        # A database failure can never be counted as a successful readiness check.
        pass
    return evidence


def readiness_checks() -> dict[str, bool]:
    checks = _database_evidence()
    checks.update({
        "s3_configured": bool(
            os.getenv("S3_BUCKET")
            and os.getenv("S3_ACCESS_KEY_ID")
            and os.getenv("S3_SECRET_ACCESS_KEY")
        ),
        "stripe_live_key_set": os.getenv("STRIPE_SECRET_KEY", "").startswith("sk_live_"),
        "docusign_configured": bool(
            os.getenv("DOCUSIGN_INTEGRATION_KEY") and os.getenv("DOCUSIGN_USER_ID")
        ),
        # These states require real account, policy, and operational proof.
        # An environment flag or the existence of a Python module is insufficient.
        "bank_account_connected": False,
        "floor_controls_set": False,
        "heimdall_authority_ready": False,
        "all_modules_loaded": False,
    })
    return checks


def is_ready_to_go_live() -> bool:
    # An unverified condition is a blocker, never a successful activation.
    return all(readiness_checks().values())


def get_readiness_report() -> dict:
    checks = readiness_checks()
    passed = sum(bool(value) for value in checks.values())
    return {
        "ready": all(checks.values()),
        "passed": passed,
        "total": len(checks),
        "percentage": 100.0 * passed / len(checks),
        "checks": checks,
        "unverified": [name for name, passed in checks.items() if not passed],
        "recommendation": (
            "Ready for review" if all(checks.values()) else
            "BLOCKED: verify every failed control before enabling live operations"
        ),
    }
