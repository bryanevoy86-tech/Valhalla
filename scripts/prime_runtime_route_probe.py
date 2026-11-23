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
    "stripe_delivery_revoke": ("POST", "/api/governance/floor/stripe-orders/{order_id}/delivery/revoke"),
    "stripe_delivery_authorize": ("POST", "/api/governance/floor/stripe-orders/{order_id}/delivery"),
    "weweb_paid_product": ("GET", "/api/weweb/paid-products/{tenant_id}/{order_id}"),
    "weweb_acknowledge_paid_product": ("POST", "/api/weweb/paid-products/{tenant_id}/{order_id}/acknowledge"),
    "stripe_bank_batch": ("POST", "/api/governance/floor/stripe-bank-batches/reconcile"),
    "stripe_payout_readback": ("POST", "/api/governance/floor/stripe-orders/{order_id}/payout-readback/{payout_id}"),
    "weweb_owner_stripe_order": ("GET", "/api/weweb/owner-stripe-orders/{order_id}"),
    "stripe_order_binding": ("POST", "/api/governance/floor/stripe-orders"),
    "stripe_order_inspection": ("GET", "/api/governance/floor/stripe-orders/{order_id}"),
    "stripe_financial_webhook": ("POST", "/webhooks/stripe"),
    "stripe_processor_readback": ("POST", "/api/governance/floor/stripe-events/{event_id}/processor-readback"),
    "weweb_owner_funding_source": ("POST", "/api/weweb/owner-startup/funding-evidence"),
    "weweb_owner_funding_review": ("POST", "/api/weweb/owner-startup/funding-review"),
    "weweb_owner_commercial_targets": ("POST", "/api/weweb/owner-startup/commercial-targets"),
    "pantheon_assign": ("POST", "/api/prime/pantheon/assignments"),
    "pantheon_challenge": ("POST", "/api/prime/pantheon/reports/{event_id}/challenge"),
    "provider_stage_probe": ("POST", "/api/prime/provider-intelligence/stage-probes"),
    "tax_opinion_provenance": ("POST", "/tax-bridge/opinions/{opinion_id}/provenance"),
    "tax_opinion_reliance_approve": ("POST", "/tax-bridge/opinions/{opinion_id}/reliance"),
    "tax_opinion_reliance_check": ("POST", "/tax-bridge/opinions/{opinion_id}/reliance/{approval_id}/check"),
    "tax_opinion_reliance_revoke": ("POST", "/tax-bridge/opinions/{opinion_id}/reliance/{approval_id}/revoke"),
    "market_forecast": ("POST", "/api/prime/norns/market/forecasts"),
    "economic_assessment": ("POST", "/api/prime/economy/assessment"),
    "weweb_owner_message": ("POST", "/api/weweb/owner-conversations/{conversation_id}/turns"),
    "weweb_owner_attachment_list": ("GET", "/api/weweb/owner-conversations/{conversation_id}/attachments"),
    "weweb_owner_upload": ("POST", "/api/weweb/owner-conversations/{conversation_id}/attachments"),
    "weweb_owner_history": ("GET", "/api/weweb/owner-conversations/{conversation_id}/turns"),
    "economic_release": ("POST", "/api/prime/economy/reservation-releases"),
    "economic_portfolio_exposure": ("GET", "/api/prime/economy/portfolio-exposure"),
    "foundry_source_intake": ("POST", "/api/prime/foundry/intake"),
    "foundry_fixture_settlement": ("POST", "/api/prime/foundry/rehearsal/orders/{order_id}/settlement-fixtures"),
    "foundry_closed_checkout_proof": ("GET", "/api/prime/foundry/rehearsal/orders/{order_id}/closed-checkout-proof"),
    "foundry_support_resolution": ("POST", "/api/prime/foundry/rehearsal/orders/{order_id}/support-resolution"),
    "foundry_fulfillment_exception": ("POST", "/api/prime/foundry/rehearsal/orders/{order_id}/fulfillment-exception"),
    "foundry_rehearsal_cost": ("POST", "/api/prime/foundry/rehearsal/orders/{order_id}/cost-fixtures"),
    "treasury_statement_fixture": ("POST", "/api/governance/floor/treasury/statement-fixtures"),
    "economic_containment": ("POST", "/api/prime/economy/containment"),
    "economic_decisions": ("POST", "/api/prime/economy/decisions"),
    "economic_mandates": ("POST", "/api/prime/economy/mandates"),
    "market_evidence": ("POST", "/api/prime/market/evidence"),
    "wealth_scenario": ("POST", "/api/governance/floor/wealth/scenarios"),
    "market_investment_replay": ("POST", "/api/prime/market/replays/investment"),
    "market_fx_replay": ("POST", "/api/prime/market/replays/fx"),
    "foundry_evidence": ("POST", "/api/prime/foundry/evidence"),
    "foundry_consumer_research": ("POST", "/api/prime/foundry/evidence/{evidence_id}/consumer-research"),
    "foundry_candidate": ("GET", "/api/prime/foundry/reports/{report_id}/candidate/{evidence_id}"),
    "foundry_campaign_summary": ("POST", "/api/prime/foundry/rehearsal/campaigns/{campaign_id}/summary"),
    "foundry_acquisition_plan": ("POST", "/api/prime/foundry/rehearsal/campaigns/{campaign_id}/acquisition-plan"),
    "foundry_acquisition_settled": ("POST", "/api/prime/foundry/rehearsal/campaigns/{campaign_id}/settled-review"),
    "foundry_acquisition_comparisons": ("POST", "/api/prime/foundry/rehearsal/campaign-comparisons"),
    "foundry_acquisition_comparison_review": ("POST", "/api/prime/foundry/rehearsal/campaign-comparisons/review-artifact"),
    "foundry_acquisition_reviewed_comparison": ("POST", "/api/prime/foundry/rehearsal/campaign-comparisons/reviewed"),
    "foundry_acquisition_suppression": ("POST", "/api/prime/foundry/rehearsal/consent-suppressions"),
    "foundry_acquisition_channel_intent": ("POST", "/api/prime/foundry/rehearsal/channel-intents"),
    "foundry_acquisition_channel_fixture_receipt": ("POST", "/api/prime/foundry/rehearsal/channel-fixture-receipts"),
    "weweb_owner_acquisition_settled": ("POST", "/api/weweb/owner-acquisition/{campaign_id}/settled-review"),
    "weweb_owner_acquisition_comparison": ("POST", "/api/weweb/owner-acquisition/comparisons"),
    "foundry_payment_rehearsal": ("POST", "/api/prime/foundry/rehearsal/payment-fixtures"),
    "saas_tenant_entitlement": ("GET", "/saas/tenant-entitlements/{tenant_id}/access/{module_key}"),
    "treasury_trajectory": ("GET", "/api/governance/floor/trajectory/month"),
    "weweb_owner_briefing": ("GET", "/api/weweb/owner-briefing"),
    "weweb_owner_document_stage": ("POST", "/api/weweb/owner-conversations/{conversation_id}/attachments/{attachment_id}/requests"),
    "weweb_owner_document_status": ("GET", "/api/weweb/owner-document-requests/{request_id}"),
    "weweb_owner_document_apply": ("POST", "/api/weweb/owner-document-requests/{request_id}/apply"),
    "weweb_owner_prime_decision": ("GET", "/api/weweb/owner-prime-decisions/{decision_id}"),
    "weweb_owner_specialist_receipt": ("GET", "/api/weweb/owner-specialist-schedules/{schedule_id}"),
    "weweb_owner_pantheon_reports": ("GET", "/api/weweb/owner-pantheon/reports"),
    "weweb_owner_attention": ("GET", "/api/weweb/owner-attention"),
    "weweb_owner_attention_ack": ("POST", "/api/weweb/owner-attention/acknowledge"),
    "weweb_owner_startup": ("POST", "/api/weweb/owner-startup/compare"),
    "weweb_owner_startup_independence": ("POST", "/api/weweb/owner-startup/independence-review"),
    "weweb_owner_operating_scope": ("POST", "/api/weweb/owner-operating-scope"),
    "weweb_owner_personal_allocation": ("POST", "/api/weweb/owner-personal-allocation"),
    "personal_allocation_receipt": ("POST", "/api/governance/floor/wealth/personal-allocation-receipts"),
    "personal_allocation_independent_review": ("POST", "/api/governance/floor/wealth/personal-allocation-review-artifact"),
    "provider_prices": ("POST", "/api/prime/provider-intelligence/price-quotes"),
    "provider_staging_selection": ("POST", "/api/prime/provider-intelligence/select-staging-candidate"),
    "norns_holdout": ("POST", "/api/prime/norns/forecasts/{forecast_id}/holdout"),
    "provider_synthetic_evidence": ("POST", "/api/prime/provider-intelligence/evidence"),
    "provider_suitability": ("GET", "/api/prime/provider-intelligence/recommendations"),
    "norns_forecast_create": ("POST", "/api/prime/norns/forecasts"),
    "norns_calibration": ("GET", "/api/prime/norns/calibration"),
    "owner_thread_create": ("POST", "/api/jarvis/conversations"),
    "owner_thread_list": ("GET", "/api/jarvis/conversations"),
    "owner_turn_send": ("POST", "/api/jarvis/conversations/{conversation_id}/turns"),
    "owner_turn_history": ("GET", "/api/jarvis/conversations/{conversation_id}/turns"),
    "owner_memory_save": ("POST", "/api/jarvis/conversations/{conversation_id}/memory"),
    "owner_memory_recall": ("GET", "/api/jarvis/conversations/{conversation_id}/memory"),
    "owner_attachment_upload": ("POST", "/api/jarvis/conversations/{conversation_id}/attachments"),
    "owner_attachment_list": ("GET", "/api/jarvis/conversations/{conversation_id}/attachments"),
    "owner_attachment_download": ("GET", "/api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}/download"),
    "owner_attachment_review": ("POST", "/api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}/review"),
    "owner_attachment_delete": ("DELETE", "/api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}"),
    "owner_attachment_extract": ("POST", "/api/jarvis/conversations/{conversation_id}/attachments/{attachment_id}/extract"),
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
    "loki_reviewer_queue": ("GET", "/loki/worker/reviews"),
    "loki_reviewer_receipt": ("POST", "/loki/worker/reviews/{review_id}/result"),
    "loki_reconsideration": ("POST", "/loki/reviews/{review_id}/reconsider"),
    "owner_identity": ("POST", "/api/weweb/login"),
    "universal_phase3": ("GET", "/api/completion/legacy-instances"),
    "factory_draft_queue": ("POST", "/api/business-factory/listing-drafts"),
    "product_artifact_stage": ("POST", "/api/business-factory/product-artifacts"),
    "product_artifact_read": ("GET", "/api/business-factory/product-artifacts/{artifact_id}/download"),
    "factory_startup_enrollment": ("POST", "/api/business-factory/mandates/enroll"),
    "factory_execution": ("POST", "/api/business-factory/actions/run-once"),
    "legacy_playbook_rehearsal": ("POST", "/api/prime/legacy-playbooks"),
    "legacy_playbook_receipt": ("GET", "/api/prime/legacy-playbooks/{target_id}"),
    "specialist_schedule_create": ("POST", "/api/prime/specialist-schedules"),
    "specialist_schedule_status": ("GET", "/api/prime/specialist-schedules/{schedule_id}"),
    "specialist_schedule_report": ("GET", "/api/prime/specialist-schedules/{schedule_id}/reports/{report_event_id}"),
    "specialist_schedule_cancel": ("DELETE", "/api/prime/specialist-schedules/{schedule_id}"),
    "marketing_registry": ("GET", "/marketing/campaigns"),
    "media_registry": ("POST", "/media/content"),
    "saas_plan_registry": ("GET", "/saas/plans"),
    "builder": ("GET", "/builder/tasks"),
    "builder_assignment": ("POST", "/builder/assignments"),
    "builder_candidate_prepare": ("POST", "/builder/assignments/prepare"),
    "builder_assignment_claim": ("POST", "/builder/assignments/claim"),
    "builder_review_handoff": ("POST", "/builder/assignments/{assignment_id}/review-handoff"),
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
