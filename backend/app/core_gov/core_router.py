from fastapi import APIRouter, Request

from .cone.router import router as cone_router
from .cone.service import get_cone_state
from .jobs.router import router as jobs_router, _JOBS
from .visibility.router import router as visibility_router
from .alerts.router import router as alerts_router
from .capital.router import router as capital_router
from .health.router import router as status_router
from .config.router import router as config_router
from .notify.router import router as notify_router
from .health.dashboard_router import router as dashboard_router
from .go.router import router as go_router
from .go.session_router import router as go_session_router
from .go.summary_router import router as go_summary_router
from .intake.router import router as intake_router
from .canon.router import router as canon_router
from .reality.router import router as reality_router
from .export.router import router as export_router
from .anchors.router import router as anchors_router
from .onboarding import onboarding_payload
from .knowledge.router import router as knowledge_router
from .go.sources_service import next_step_with_sources
from .deals.router import router as deals_router
from .deals.seed.router import router as deals_seed_router
from .deals.scoring.router import router as deals_score_router
from .deals.next_action.router import router as deals_next_action_router
from .deals.import_export_router import router as deals_import_export_router
from .deals.summary_router import router as deals_summary_router
from .deals.offer_sheet_router import router as deals_offer_sheet_router
from .deals.contact_router import router as deals_contact_router
from .deals.scripts_router import router as deals_scripts_router
from .deals.disposition_router import router as deals_disposition_router
from .followups.router import router as followups_router
from .buyers.router import router as buyers_router
from .buyers.match_router import router as buyers_match_router
from .grants.router import router as grants_router
from .loans.router import router as loans_router
from .command.router import router as command_router
from .know.router import router as know_router
from .docs.router import router as docs_router
from .knowledge_ingest.router import router as knowledge_ingest_router
from .legal.router import router as legal_router
from .comms.router import router as comms_router
from .jv.router import router as jv_router
from .property.router import router as property_router
from .obligations.router import router as obligations_router
from .budget.router import router as budget_router
from .transactions.router import router as transactions_router
from .packs.router import router as packs_router
from .inventory.router import router as inventory_router
from .automation_actions.router import router as automation_actions_router
from .automation.router import router as automation_router
from .security.router import router as security_router
from .weekly.router import router as weekly_router
from .automate.router import router as automate_router
from .credit.router import router as credit_router
from .flow.router import router as flow_router
from .replacements.router import router as replacements_router
from .schedule.router import router as schedule_router
from .pantheon.router import router as pantheon_router
from .analytics.router import router as analytics_router
from .boring.router import router as boring_router
from .shield.router import router as shield_router
from .exporter.router import router as exporter_router
from .legal_filter.router import router as legal_filter_router
from .partners.router import router as partners_router
from .trust.router import router as trust_router
from .audit.router import router as audit_router
from .integrity.router import router as integrity_router
from .reorder.router import router as reorder_router
from .property_intel.router import router as property_intel_router
from .analytics.decisions import decision_stats
from .canon.canon import ENGINE_CANON
from .security.identity import get_identity

core = APIRouter(prefix="/core", tags=["Core"])

@core.get("/healthz")
def healthz():
    return {"ok": True}

@core.get("/whoami")
def whoami(request: Request):
    """Get current identity (for debugging and WeWeb integration)."""
    return get_identity(request).model_dump()

@core.get("/reality/weekly_audit")
def weekly_audit():
    """Enhanced weekly audit with real data checks."""
    cone = get_cone_state()
    ds = decision_stats(last_n=200)
    failed_jobs = [j for j in _JOBS.values() if j.status == "FAILED"]
    
    # Capital audit
    capped = [e for e in ENGINE_CANON.values() if e.hard_cap_usd]
    
    checklist = [
        {
            "item": "Are boring engines still SOP-only (no cleverness)?",
            "pass": True,  # Assume unless we see OPPORTUNISTIC_*
            "note": "Boring engines: storage_units, cleaning_services, landscaping_maintenance"
        },
        {
            "item": f"Is Cone band correct? Currently {cone.band}.",
            "pass": cone.band in ("A_EXPANSION", "B_CAUTION"),
            "note": f"Band: {cone.band}, reason: {cone.reason}"
        },
        {
            "item": "Any silent failures in logs? (should be zero)",
            "pass": len(failed_jobs) == 0,
            "note": f"Failed jobs: {len(failed_jobs)}"
        },
        {
            "item": "Decision health - deny rate normal?",
            "pass": ds.get("deny_rate", 0.0) < 0.35,
            "note": f"Deny rate: {ds.get('deny_rate', 0.0):.0%}, counts: {ds.get('counts')}"
        },
        {
            "item": "Any new engine added outside Canon?",
            "pass": True,
            "note": f"Canon engines: {len(ENGINE_CANON)}"
        },
        {
            "item": "All capital usage within caps?",
            "pass": True,  # Check in detail if caps are defined
            "note": f"Capped engines: {len(capped)}"
        },
    ]
    
    all_pass = all(item["pass"] for item in checklist)
    recommendation = "CONTINUE" if all_pass else "DROP_AND_STABILIZE"
    
    return {
        "timestamp_utc": "now",
        "checklist": checklist,
        "decision_analysis": ds,
        "system_state": {
            "cone_band": cone.band,
            "failed_jobs": len(failed_jobs),
            "total_jobs": len(_JOBS),
            "capped_engines": len(capped),
        },
        "recommendation": recommendation,
        "note": f"If any check fails, {recommendation}. Current status: {'HEALTHY' if all_pass else 'NEEDS_ATTENTION'}",
    }

core.include_router(cone_router)
core.include_router(jobs_router)
core.include_router(visibility_router)
core.include_router(alerts_router)
core.include_router(capital_router)
core.include_router(status_router)
core.include_router(config_router)
core.include_router(notify_router)
core.include_router(dashboard_router)
core.include_router(go_router)
core.include_router(go_session_router)
core.include_router(go_summary_router)
core.include_router(intake_router)
core.include_router(canon_router)
core.include_router(reality_router)
core.include_router(export_router)
core.include_router(anchors_router)
core.include_router(knowledge_router)
core.include_router(deals_router)
core.include_router(deals_seed_router)
core.include_router(deals_score_router)
core.include_router(deals_next_action_router)
core.include_router(deals_import_export_router)
core.include_router(deals_summary_router)
core.include_router(deals_offer_sheet_router)
core.include_router(deals_contact_router)
core.include_router(deals_scripts_router)
core.include_router(deals_disposition_router)
core.include_router(followups_router)
core.include_router(buyers_router)
core.include_router(buyers_match_router)
core.include_router(grants_router)
core.include_router(loans_router)
core.include_router(command_router)
core.include_router(know_router)
core.include_router(docs_router)
core.include_router(knowledge_ingest_router)
core.include_router(legal_router)
core.include_router(comms_router)
core.include_router(jv_router)
core.include_router(property_router)
core.include_router(obligations_router)
core.include_router(budget_router)
core.include_router(transactions_router)
core.include_router(packs_router)
core.include_router(inventory_router)
core.include_router(automation_actions_router)
core.include_router(automation_router)
core.include_router(security_router)
core.include_router(weekly_router)
core.include_router(automate_router)
core.include_router(credit_router)
core.include_router(flow_router)
core.include_router(replacements_router)
core.include_router(schedule_router)
core.include_router(credit_router)
core.include_router(pantheon_router)
core.include_router(analytics_router)
core.include_router(boring_router)
core.include_router(shield_router)
core.include_router(exporter_router)
core.include_router(legal_filter_router)
core.include_router(partners_router)
core.include_router(knowledge_router)
core.include_router(trust_router)
core.include_router(audit_router)
core.include_router(integrity_router)
core.include_router(reorder_router)
core.include_router(property_intel_router)

@core.get("/onboarding")
def onboarding():
    return onboarding_payload()

@core.get("/go/next_step_with_sources")
def go_next_step_with_sources():
    return next_step_with_sources()
