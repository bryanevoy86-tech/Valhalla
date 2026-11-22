"""Conservative decisions for comparable, internally settled campaign fixtures."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import HTTPException
from pydantic import Field, model_validator

from app.loki.evidence import artifact_digest
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.consumer_evidence import interval


class ComparisonIn(StrictModel):
    scope: MarketScope
    campaign_ids: list[Annotated[int, Field(strict=True, gt=0)]] = Field(min_length=2, max_length=5)
    minimum_visits: int = Field(default=40, strict=True, ge=20, le=10000)

    @model_validator(mode="after")
    def distinct_campaigns(self):
        if len(set(self.campaign_ids)) != len(self.campaign_ids):
            raise ValueError("Use distinct campaign IDs")
        return self


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
