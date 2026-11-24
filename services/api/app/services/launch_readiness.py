"""Read-only owner projection of capability-specific release gates."""
from sqlalchemy import inspect

from app.models.go_live_state import GoLiveState
from app.services.prime_business_execution import _emergency_stop_active


# Until independent release evidence has an authoritative verifier, no channel may
# derive external authority from local artifacts, feature flags or a legacy global toggle.
CHANNEL_REQUIREMENTS = {
    "discovery_and_research": ("SOURCE_RIGHTS", "INDEPENDENT_REVIEW", "PARTICIPANT_CONSENT"),
    "customer_acquisition_and_sales": ("CHANNEL_PERMISSION", "SCOPED_PARTICIPANT_IDENTITY", "CUSTOMER_TERMS", "SUPPORTED_SALES_DELIVERY"),
    "agreements_and_signatures": ("SIGNATORY_AUTHORITY", "PROFESSIONAL_REVIEW_IF_APPLICABLE", "PROVIDER_READBACK"),
    "commerce_and_fulfillment": ("VERIFIED_MERCHANT", "CUSTOMER_ENTITLEMENT", "DELIVERY_AND_SUPPORT"),
    "support_refunds_and_disputes": ("REFUND_POLICY", "PROVIDER_READBACK", "DISPUTE_ESCALATION"),
    "recurring_service": ("RENEWAL_AND_CANCELLATION", "SERVICE_LIABILITY", "PERIOD_RECONCILIATION"),
    "accounting_and_bank": ("ACCOUNTING_REVIEW", "INDEPENDENT_BANK_MATCH", "LIABILITIES_RESERVES_AND_CASH_HOLDS"),
    "expansion_and_regulated_actions": ("SEPARATE_SCOPE_AND_MANDATE", "LICENSED_AUTHORITY_IF_APPLICABLE", "INDEPENDENT_OUTCOME"),
}
COMMON_REQUIREMENTS = ("EXACT_STANDING_AUTHORITY", "COST_LIMIT", "OPERATOR_FALLBACK", "RECOVERY_AND_MONITORING",
                       "CURRENT_INDEPENDENT_ACCEPTANCE")


def capability_release_holds(db):
    state = (db.get(GoLiveState, 1) if inspect(db.connection()).has_table(GoLiveState.__tablename__) else None)
    stop = "ENGAGED" if _emergency_stop_active(db) else "CLEAR" if state is not None else "UNKNOWN"
    blockers = ["OPERATIONAL_RELEASE_EVIDENCE_NOT_CONNECTED"]
    if stop != "CLEAR":
        blockers.append("EMERGENCY_STOP_NOT_CLEAR")
    return {
        "basis": "READ_ONLY_CAPABILITY_GATES",
        "emergency_stop": stop,
        "internal_scope": {"mode": "EXISTING_DISPOSABLE_CONTROLS", "standing_authority_required": True},
        "channels": {
            name: {"status": "HELD", "requirements": [*COMMON_REQUIREMENTS, *required]}
            for name, required in CHANNEL_REQUIREMENTS.items()
        },
        "global_blockers": blockers,
        "actual_spend_minor": None,
        "verified_business_performance": None,
        "external_authority": False,
    }
