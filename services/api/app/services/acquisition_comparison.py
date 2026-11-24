"""Conservative decisions for comparable, internally settled campaign fixtures."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, model_validator
from sqlalchemy import inspect, select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.consumer_evidence import interval
from app.services.prime_business_execution import _json

REVIEWED_EVENT = "ACQUISITION_FIXTURE_REVIEWED"
REVIEWED_PREFIX = "ACQ-REVIEW-"


class ComparisonIn(StrictModel):
    scope: MarketScope
    campaign_ids: list[Annotated[int, Field(strict=True, gt=0)]] = Field(min_length=2, max_length=5)
    minimum_visits: int = Field(default=40, strict=True, ge=20, le=10000)

    @model_validator(mode="after")
    def distinct_campaigns(self):
        if len(set(self.campaign_ids)) != len(self.campaign_ids):
            raise ValueError("Use distinct campaign IDs")
        return self


class ReviewedComparisonIn(ComparisonIn):
    independent_review_id: UUID


def campaign_disposition(review, minimum_visits):
    visits = review["visits"]
    buyers = review["positive_net_orders"]
    contribution = review["contribution_minor"]
    if review["recorded_acquisition_cost_exceeds_budget"]:
        return "STOP", "RECORDED_FIXTURE_COST_EXCEEDS_LIMIT"
    if review["unresolved_orders"] or visits < minimum_visits:
        return "CONTINUE_TESTING", "SETTLEMENT_OR_SAMPLE_INCOMPLETE"
    if contribution is None:
        return "IMPROVE", "MISSING_SETTLED_CONTRIBUTION" if buyers else "NO_ATTRIBUTED_POSITIVE_NET_ORDERS"
    if contribution <= 0:
        return "STOP", "NONPOSITIVE_SETTLED_CONTRIBUTION"
    if not review["acquisition_cost_covered"]:
        return "IMPROVE", "ACQUISITION_COST_COVERAGE_INCOMPLETE"
    return "CONTINUE_TESTING", "POSITIVE_FIXTURE_PENDING_COMPARISON"


def compare_settled_campaigns(reviews, minimum_visits):
    arms = []
    for review in reviews:
        decision, reason = campaign_disposition(review, minimum_visits)
        count = review["visits"]
        arms.append({
            "campaign_id": review["campaign_id"], "settled_sha256": review["sha256"], "visits": count,
            "positive_net_orders": review["positive_net_orders"], "contribution_minor": review["contribution_minor"],
            "unresolved_orders": review["unresolved_orders"], "acquisition_cost_covered": review["acquisition_cost_covered"],
            "contribution_per_visit_minor": (
                review["contribution_minor"] // count if count and review["contribution_minor"] is not None else None
            ),
            "positive_net_order_interval": interval(review["positive_net_orders"], count) if count else None,
            "decision": decision, "reason": reason,
        })
    if not all(review["visits"] >= minimum_visits and not review["unresolved_orders"]
               for review in reviews):
        return arms

    for arm in arms:
        if arm["reason"] != "POSITIVE_FIXTURE_PENDING_COMPARISON":
            continue
        rivals = [other for other in arms if other["campaign_id"] != arm["campaign_id"]]
        strongest_rival = max(other["positive_net_order_interval"]["interval_high_bp"] for other in rivals)
        if (arm["positive_net_order_interval"]["interval_low_bp"] > strongest_rival
                and all(other["contribution_per_visit_minor"] is not None
                        and arm["contribution_per_visit_minor"] > other["contribution_per_visit_minor"] for other in rivals)):
            arm.update(decision="SCALE_REVIEW", reason="DISTINGUISHABLE_FIXTURE_CONVERSION_AND_CONTRIBUTION")
        else:
            arm["reason"] = "COMPARATIVE_EVIDENCE_INCONCLUSIVE"
    return arms


def compare_campaigns(db, request: ComparisonIn):
    from app.services.acquisition_rehearsal import AcquisitionPlanIn, make_plan, read_plan, settled_campaign

    scope = request.scope.model_dump()
    campaign_ids = sorted(request.campaign_ids)
    plans = [read_plan(db, campaign, scope) for campaign in campaign_ids]
    if any(plan is None for plan in plans):
        raise HTTPException(404, "Every comparison arm needs a scoped acquisition plan")
    keys = {(plan["request"]["demand_evidence_id"], plan["demand_sha256"],
             (plan.get("consumer_research") or {}).get("sha256")) for plan in plans}
    if len(keys) != 1:
        raise HTTPException(409, "Compare only campaigns bound to the same demand and research version")
    cohorts = []
    reviews = [settled_campaign(db, campaign, scope, cohort=cohorts) for campaign in campaign_ids]
    if len(cohorts) != len(set(cohorts)):
        raise HTTPException(409, "Comparison arms contain repeated synthetic customer references")
    demand_id, _, research_sha = next(iter(keys))
    summary = {"scope": scope, "basis": "SETTLED_CAMPAIGN_FIXTURE_COMPARISON", "demand_evidence_id": demand_id,
               "consumer_research_sha256": research_sha, "minimum_visits": request.minimum_visits,
               "arms": compare_settled_campaigns(reviews, request.minimum_visits),
               "customer_identity_coverage_complete": all(plan["request"]["channel"] == "DIRECT_OPT_IN" for plan in plans),
               "causality_verified": False, "verified_commercial_revenue": False, "external_action_authorized": False,
               "requires_independent_review": True}
    for arm, plan in zip(summary["arms"], plans):
        if arm["decision"] != "SCALE_REVIEW":
            continue
        if not summary["customer_identity_coverage_complete"]:
            arm.update(decision="CONTINUE_TESTING", reason="CUSTOMER_OVERLAP_UNVERIFIED")
            continue
        proposed = AcquisitionPlanIn.model_validate(plan["request"])
        try:
            current = make_plan(db, arm["campaign_id"], proposed, datetime.now(timezone.utc).date())
            unchanged = all(current.get(key) == plan.get(key) for key in ("demand_sha256", "consumer_research"))
        except HTTPException:
            unchanged = False
        if not unchanged:
            arm.update(decision="CONTINUE_TESTING", reason="CURRENT_DEMAND_OR_RESEARCH_UNVERIFIED")
    return {**summary, "sha256": artifact_digest("acquisition_fixture_comparison", ":".join(map(str, campaign_ids)), summary)}


def comparison_review_artifact(comparison):
    reference = comparison["sha256"]
    return {"artifact_type": "acquisition_comparison", "input_source": "acquisition-rehearsal",
            "heimdall_reference_id": reference, "raw_input": comparison,
            "artifact_sha256": artifact_digest("acquisition_comparison", reference, comparison)}


def reviewed_capital_projection(db, request: ReviewedComparisonIn):
    from app.loki.models import LokiReview
    from app.loki.review_service import reviewer_identity, verdict
    from app.routers.economic_control import assess, require_schema
    from app.services.acquisition_rehearsal import read_plan
    from app.services.prime_business_execution import _emergency_stop_active

    comparison = compare_campaigns(db, request)
    artifact = comparison_review_artifact(comparison)
    reviewer_identity()
    review = db.get(LokiReview, request.independent_review_id)
    if (review is None or review.artifact_type != artifact["artifact_type"]
            or review.heimdall_reference_id != artifact["heimdall_reference_id"]
            or review.artifact_sha256 != artifact["artifact_sha256"] or not verdict(db, review).ok_to_proceed):
        raise HTTPException(409, "Current comparison requires exact independently reviewed evidence")
    require_schema(db)
    try:
        economic = assess(request.scope, db)
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        economic = None
    blockers = economic["blockers"][:] if economic is not None else ["NO_SCOPED_ECONOMIC_MANDATE"]
    if economic is not None and economic["currency"] != "CAD":
        blockers.append("CAMPAIGN_CURRENCY_MISMATCH")
    if _emergency_stop_active(db):
        blockers.append("EMERGENCY_STOP")
    winner = next((arm["campaign_id"] for arm in comparison["arms"] if arm["decision"] == "SCALE_REVIEW"), None)
    candidate_budget = read_plan(db, winner, comparison["scope"])["request"]["experiment_budget_minor"] if winner else 0
    cap = min(candidate_budget, economic["comparison_budget_minor"]) if economic is not None and not blockers else 0
    value = {"scope": comparison["scope"], "comparison_sha256": comparison["sha256"],
             "independent_review_id": str(review.id), "independent_artifact_sha256": review.artifact_sha256,
             "economic_mandate_id": economic["mandate_id"] if economic else None,
             "economic_operation_sequence": economic["operation_sequence"] if economic else None,
             "currency": "CAD", "scale_review_candidate": winner if cap > 0 else None,
             "simulated_followup_cap_minor": cap, "blockers": sorted(set(blockers)),
             "basis": "REVIEWED_CAMPAIGN_FIXTURE_ONLY", "capital_reserved_minor": 0,
             "external_action_authorized": False, "verified_commercial_revenue": False}
    return {**value, "sha256": artifact_digest("reviewed_campaign_fixture", str(review.id), value)}


def observe_reviewed_comparisons(db, scope):
    journal = LegacyOrchestrationEvent
    if not inspect(db.connection()).has_table(journal.__tablename__):
        return []
    rows = db.scalars(select(journal).where(journal.event_type == REVIEWED_EVENT,
                      journal.legacy_instance_id == scope["legacy_instance_id"]).order_by(journal.id.desc()).limit(20))
    reviewed = []
    for row in rows:
        receipt = _json(row.payload_json, {})
        if not isinstance(receipt, dict) or receipt.get("scope") != scope:
            continue
        value = {key: item for key, item in receipt.items() if key != "sha256"}
        expected = artifact_digest("reviewed_campaign_fixture", value.get("independent_review_id"), value)
        if (receipt.get("sha256") != expected or row.event_id != REVIEWED_PREFIX + expected
                or receipt.get("capital_reserved_minor") != 0 or receipt.get("external_action_authorized") is not False):
            reviewed.append({"status": "EVIDENCE_HOLD", "scope": scope, "external_action_authorized": False})
        else:
            reviewed.append({**receipt, "status": "HISTORICAL_REVIEW_ONLY"})
    return reviewed[:5]
