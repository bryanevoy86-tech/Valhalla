#!/usr/bin/env python3
"""Read-only route-contract probe for the canonical Valhalla FastAPI app.

This probe never calls business endpoints, sends money, emails or model
requests. --import-app DOES execute Python imports, so run it in an isolated
test/staging environment with test DB credentials and no live provider keys.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services/api"

# Exact backend API contracts as authored in the working branch. These
# checks establish registration, NOT successful execution or authorization.
MANDATORY_ENDPOINTS = {
    "release_state": ("GET", "/governance/go-live/state"),
    "release_checklist": ("GET", "/governance/go-live/checklist"),
    "release_enable": ("POST", "/governance/go-live/enable"),
    "release_disable": ("POST", "/governance/go-live/disable"),
    "emergency_engage": ("POST", "/governance/go-live/kill-switch/engage"),
    "emergency_release": ("POST", "/governance/go-live/kill-switch/release"),
    "integrity_inspection": ("GET", "/api/system/self-check"),
    "integrity_audit": ("POST", "/api/system/self-check"),
    "private_deal_intake": ("POST", "/flow/full_deal_pipeline"),
    "private_deal_status": ("GET", "/workflow/deal_status/{backend_deal_id}"),
    "metadata_complete": ("POST", "/system/status/complete"),
    "metadata_incomplete": ("POST", "/system/status/incomplete"),
    "loki_audit_submission": ("POST", "/loki/reviews"),
    "loki_audit_verdict": ("GET", "/loki/reviews/{review_id}/verdict"),
    "owner_identity": ("POST", "/api/weweb/login"),
    "universal_phase3": ("GET", "/api/completion/legacy-instances"),
    "factory_draft_queue": ("POST", "/api/business-factory/listing-drafts"),
    "factory_execution": ("POST", "/api/business-factory/actions/run-once"),
    "marketing_registry": ("GET", "/marketing/campaigns"),
    "media_registry": ("POST", "/media/content"),
    "saas_plan_registry": ("GET", "/saas/plans"),
    "builder": ("GET", "/builder/tasks"),
    "system_readiness": ("GET", "/readyz"),
    "pantheon_king": ("POST", "/api/governance/king/evaluate"),
    "pantheon_queen": ("POST", "/api/governance/queen/evaluate"),
    "pantheon_odin": ("POST", "/api/governance/odin/evaluate"),
    "pantheon_loki": ("POST", "/api/governance/loki/evaluate"),
    "pantheon_tyr": ("POST", "/api/governance/tyr/evaluate"),
    "pantheon_war_table": ("POST", "/api/governance/evaluate_all"),
}


def inspect_route_contract(routes) -> dict:
    available = {
        (str(method), str(route.path))
        for route in routes
        for method in getattr(route, "methods", [])
        if getattr(route, "path", None)
    }
    result = {}
    for capability, (method, path) in MANDATORY_ENDPOINTS.items():
        result[capability] = {
            "method": method,
            "path": path,
            "registered": (method, path) in available,
        }
    missing = sorted(name for name, entry in result.items() if not entry["registered"])
    return {
        "ok": len(missing) == 0,
        "registered": len(result) - len(missing),
        "required": len(result),
        "missing": missing,
        "checks": result,
        "warning": "Route registration is not a successful provider operation or business outcome.",
    }


def load_canonical_app() -> dict:
    if str(API_ROOT) not in sys.path:
        sys.path.insert(0, str(API_ROOT))
    try:
        app_module = importlib.import_module("app.main")
    except Exception as exc:
        # Deliberately show only type; an exception string can expose a
        # connection URL or secret embedded in driver errors.
        return {
            "ok": False,
            "reason": "CANONICAL_APP_IMPORT_FAILED",
            "exception_type": type(exc).__name__,
            "warning": "No operational or business success proven",
        }
    try:
        from sqlalchemy.orm import configure_mappers

        configure_mappers()
    except Exception as exc:
        return {
            "ok": False,
            "reason": "CANONICAL_ORM_CONFIGURATION_FAILED",
            "exception_type": type(exc).__name__,
        }

    app = app_module.app
    report = inspect_route_contract(app.routes)
    report["orm_mappers_configured"] = True
    integrity = getattr(app.state, "router_integrity", None)
    report["critical_router_integrity"] = integrity
    report["ok"] = bool(report["ok"] and integrity and integrity.get("ready"))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-app", action="store_true", help="import full backend; use isolated environment")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", default="", help="optional local report file; never secrets")
    args = parser.parse_args()

    result = load_canonical_app() if args.import_app else {
        "ok": False,
        "reason": "NOT_EXECUTED",
        "required": len(MANDATORY_ENDPOINTS),
        "warning": "Run with --import-app in an isolated environment to perform actual source imports",
    }
    output = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(output)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
