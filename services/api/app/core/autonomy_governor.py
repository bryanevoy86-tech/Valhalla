"""Deterministic Heimdall Prime autonomy governor (phase-one policy boundary).

Use AFTER deriving inputs from trusted backend policy/state and BEFORE
dispatching an effect. Never let an LLM set "owner_approval_verified" or
"source_rights_verified" itself. Verdicts are not provider receipts.

This first release can ALLOW only safe bounded internal actions, RESEARCH_READ,
and EVALUATE. Any unconnected external provider effect remains BLOCKED or
REVIEW_REQUIRED. This is deliberate: writing the policy does not integrate
payments, publishing, marketing or signing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Action = Literal[
    "RESEARCH_READ", "EVALUATE", "INTERNAL_DRAFT",
    "EXTERNAL_POST", "CUSTOMER_OUTREACH", "CUSTOMER_SUPPORT",
    "PAYMENT_CAPTURE", "PAYOUT", "CONTRACT_SIGN", "CODE_DEPLOY",
    "DELETE_CUSTOMER_DATA",
]
Mode = Literal["SHADOW", "BOUNDED", "HALTED"]
Verdict = Literal["ALLOW", "ABSTAIN", "REVIEW_REQUIRED", "BLOCK"]

READ_ACTIONS = frozenset({"RESEARCH_READ", "EVALUATE"})
INTERNAL_ACTIONS = frozenset({"INTERNAL_DRAFT"})
EXTERNAL_ACTIONS = frozenset({
    "EXTERNAL_POST", "CUSTOMER_OUTREACH", "CUSTOMER_SUPPORT",
    "PAYMENT_CAPTURE", "PAYOUT", "CONTRACT_SIGN", "CODE_DEPLOY",
    "DELETE_CUSTOMER_DATA",
})
# These cannot be automatically enabled by a model recommendation,
# even if the system is in BOUNDED mode.
OWNER_ONLY_ACTIONS = frozenset({
    "PAYMENT_CAPTURE", "PAYOUT", "CONTRACT_SIGN", "CODE_DEPLOY",
    "DELETE_CUSTOMER_DATA",
})
ALL_ACTIONS = READ_ACTIONS | INTERNAL_ACTIONS | EXTERNAL_ACTIONS


@dataclass(frozen=True)
class ActionIntent:
    action: str
    mode: str = "SHADOW"
    action_id: str = ""
    business_id: str = ""
    legacy_id: str = ""
    # These must originate in actual policy/owner/tenant database evidence.
    business_scope_verified: bool = False
    tenant_scope_verified: bool = False
    owner_approval_verified: bool = False
    # Inputs for read-only analysis, sourced from a governed source registry.
    source_rights_verified: bool = False
    independent_sources: int = 0
    confidence: float | None = None
    # These must come from durable ledger/scheduler/provider state, not AI text.
    planned_cost_cents: int = 0
    remaining_budget_cents: int = 0
    consent_verified: bool = False
    circuit_breaker_open: bool = False
    outcome_uncertain: bool = False
    system_integrity_verified: bool = True
    emergency_stop: bool = False
    untrusted_source_requests_tool_action: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    verdict: Verdict
    reason: str
    external_effects_authorized: bool = False

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "external_effects_authorized": False,
        }


def decide(intent: ActionIntent) -> PolicyDecision:
    """Return conservative, explanatory policy decision without side effects."""
    if intent.action not in ALL_ACTIONS or intent.mode not in {"SHADOW", "BOUNDED", "HALTED"}:
        return PolicyDecision("BLOCK", "UNKNOWN_ACTION_OR_MODE")
    if intent.mode == "HALTED" or intent.emergency_stop:
        return PolicyDecision("BLOCK", "EMERGENCY_STOP_ACTIVE")
    if not intent.system_integrity_verified:
        return PolicyDecision("BLOCK", "SYSTEM_INTEGRITY_NOT_VERIFIED")
    if intent.circuit_breaker_open:
        return PolicyDecision("BLOCK", "CIRCUIT_BREAKER_OPEN")
    if intent.outcome_uncertain:
        return PolicyDecision("BLOCK", "PRIOR_OUTCOME_UNKNOWN_RECONCILE_FIRST")
    if intent.untrusted_source_requests_tool_action:
        return PolicyDecision("BLOCK", "UNTRUSTED_SOURCE_INSTRUCTION")
    if not intent.business_scope_verified or not intent.tenant_scope_verified:
        return PolicyDecision("BLOCK", "BUSINESS_OR_TENANT_SCOPE_NOT_VERIFIED")
    if (
        isinstance(intent.planned_cost_cents, bool)
        or isinstance(intent.remaining_budget_cents, bool)
        or not isinstance(intent.planned_cost_cents, int)
        or not isinstance(intent.remaining_budget_cents, int)
        or intent.planned_cost_cents < 0
        or intent.remaining_budget_cents < 0
    ):
        return PolicyDecision("BLOCK", "INVALID_COST_OR_BUDGET")
    if intent.planned_cost_cents > intent.remaining_budget_cents:
        return PolicyDecision("BLOCK", "BUDGET_EXCEEDED")
    if (
        isinstance(intent.independent_sources, bool)
        or not isinstance(intent.independent_sources, int)
        or intent.independent_sources < 0
    ):
        return PolicyDecision("BLOCK", "INVALID_SOURCE_COUNT")
    if (
        intent.confidence is not None
        and (isinstance(intent.confidence, bool)
             or not isinstance(intent.confidence, (int, float))
             or not 0 <= intent.confidence <= 1)
    ):
        return PolicyDecision("BLOCK", "INVALID_CONFIDENCE")

    if intent.action in EXTERNAL_ACTIONS:
        if intent.mode == "SHADOW":
            return PolicyDecision("BLOCK", "SHADOW_MODE_NO_EXTERNAL_EFFECTS")
        if intent.action in OWNER_ONLY_ACTIONS:
            return PolicyDecision("REVIEW_REQUIRED", "OWNER_ONLY_HIGH_IMPACT_ACTION")
        if not intent.owner_approval_verified:
            return PolicyDecision("REVIEW_REQUIRED", "OWNER_APPROVAL_MISSING")
        if intent.action == "CUSTOMER_OUTREACH" and not intent.consent_verified:
            return PolicyDecision("BLOCK", "OUTREACH_CONSENT_NOT_VERIFIED")
        if intent.action == "EXTERNAL_POST" and (
            not intent.source_rights_verified or intent.independent_sources < 1
        ):
            return PolicyDecision("REVIEW_REQUIRED", "PUBLISHING_EVIDENCE_INSUFFICIENT")
        # Nobody may infer external success or permission to dispatch from
        # this pure preflight. Use real provider + durable entitlement guards.
        return PolicyDecision("REVIEW_REQUIRED", "EXTERNAL_PROVIDER_GATE_NOT_CONNECTED")

    if intent.action == "INTERNAL_DRAFT":
        if not intent.owner_approval_verified:
            return PolicyDecision("REVIEW_REQUIRED", "INTERNAL_DRAFT_APPROVAL_REQUIRED")
        return PolicyDecision("ALLOW", "BOUNDED_INTERNAL_DRAFT_ONLY")

    if not intent.source_rights_verified:
        return PolicyDecision("ABSTAIN", "SOURCE_RIGHTS_UNVERIFIED")
    if intent.action == "RESEARCH_READ":
        return PolicyDecision("ALLOW", "GOVERNED_READ_ONLY_RESEARCH")
    if intent.action == "EVALUATE":
        if intent.independent_sources < 2 or intent.confidence is None or intent.confidence < 0.75:
            return PolicyDecision("ABSTAIN", "INDEPENDENT_EVIDENCE_OR_CONFIDENCE_INSUFFICIENT")
        return PolicyDecision("ALLOW", "EVALUATION_ONLY_NO_EXTERNAL_EFFECTS")
    return PolicyDecision("BLOCK", "UNRECOGNIZED_OPERATION")


def require_internal_draft(
    *,
    action_id: str,
    business_id: str,
    legacy_id: str,
    approved: bool,
    emergency_stop: bool,
) -> PolicyDecision:
    """Convenience entry for trusted DB-backed Business Factory task worker."""
    return decide(ActionIntent(
        action="INTERNAL_DRAFT",
        action_id=action_id,
        business_id=business_id,
        legacy_id=legacy_id,
        business_scope_verified=bool(business_id and legacy_id),
        tenant_scope_verified=bool(business_id and legacy_id),
        owner_approval_verified=approved,
        emergency_stop=emergency_stop,
    ))
