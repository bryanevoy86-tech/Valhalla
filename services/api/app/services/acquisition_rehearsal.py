"""Link a private acquisition plan to scoped discovery and settled fixture outcomes."""
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import inspect, select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.foundry_checkout import FoundryCampaignVisit, FoundryRehearsalOrder
from app.models.foundry_evidence import FoundryEvidence
from app.models.marketing import MarketingCampaign
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.foundry_discovery import checked_evidence, demand_evidence, economics
from app.services.prime_business_execution import _json
from app.services.specialist_triggers import outcome_scope_key


EVENT_TYPE = "ACQUISITION_FIXTURE_PLAN"


class AcquisitionPlanIn(StrictModel):
    scope: MarketScope
    demand_evidence_id: UUID
    channel: Literal["ORGANIC", "DIRECT_OPT_IN", "MARKETPLACE", "AFFILIATE", "PAID"]
    experiment_budget_minor: int = Field(strict=True, ge=0, le=100_000_000)
    stop_after_visits: int = Field(strict=True, ge=1, le=10000)


def plan_reference(campaign_id):
    return f"ACQ-PLAN-{campaign_id}"


def make_plan(db, campaign_id, request, today: date):
    scope = request.scope.model_dump()
    if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
        raise HTTPException(503, "Demand evidence storage unavailable")
    campaign = db.get(MarketingCampaign, campaign_id)
    row = db.get(FoundryEvidence, request.demand_evidence_id)
    if campaign is None or row is None:
        raise HTTPException(404, "Campaign or demand record not found")
    evidence = checked_evidence(row, scope, today, db=db)
    demand = demand_evidence(evidence)
    if demand is None or not demand["demand_count"] or evidence.currency != "CAD":
        raise HTTPException(409, "Current sourced CAD demand evidence with observed interest is required")
    if request.experiment_budget_minor > evidence.test_cost:
        raise HTTPException(409, "Proposed campaign budget exceeds the sourced validation estimate")
    return {
        "campaign_id": campaign_id, "request": request.model_dump(mode="json"), "demand_sha256": row.digest,
        "target_buyer_segment": demand["buyer_segment"], "source_id": demand["source_id"],
        "demand_sample_count": demand["sample_count"], "demand_positive_count": demand["demand_count"],
        "unit_economics": economics(evidence), "basis": "INTERNAL_ACQUISITION_REHEARSAL",
        "external_outreach_authorized": False, "spend_authorized": False, "publication_authorized": False,
    }


def read_plan(db, campaign_id, scope):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return None
    ref = plan_reference(campaign_id)
    event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=ref))
    if event is None:
        return None
    plan = _json(event.payload_json, {})
    digest = plan.pop("sha256", None)
    if (event.event_type != EVENT_TYPE or event.legacy_instance_id != scope["legacy_instance_id"]
            or plan.get("request", {}).get("scope") != scope
            or digest != artifact_digest("acquisition_fixture_plan", ref, plan)):
        raise HTTPException(409, "Campaign plan integrity or scope mismatch")
    return {**plan, "sha256": digest}


def settled_campaign(db, campaign_id, scope):
    from app.routers.foundry_checkout import closed_checkout_proof

    plan = read_plan(db, campaign_id, scope)
    if plan is None:
        raise HTTPException(404, "Scoped acquisition rehearsal plan not found")
    visit = FoundryCampaignVisit
    linked = select(visit).where(visit.campaign_id == campaign_id, visit.scope_key == outcome_scope_key(scope))
    visits = db.scalars(linked.order_by(visit.id).limit(10001)).all()
    if len(visits) > 10000:
        raise HTTPException(409, "Campaign exceeds the rehearsal evidence limit")
    order_ids = [item.order_id for item in visits if item.order_id is not None]
    if len(order_ids) > 100:
        raise HTTPException(409, "Campaign exceeds the rehearsal order limit")
    settled, pending = [], 0
    for order_id in order_ids:
        order = db.get(FoundryRehearsalOrder, order_id)
        if order is None or order.captured_minor == 0:
            pending += 1
            continue
        try:
            settled.append(closed_checkout_proof(db, order_id, scope=scope))
        except HTTPException as exc:
            if exc.status_code not in {404, 409}:
                raise
            pending += 1
    captured = len(settled)
    retained = sum(proof["net_minor"] > 0 for proof in settled)
    acquisition_cost = sum(cost["amount_minor"] for proof in settled for cost in proof["costs"]
                           if cost["category"] == "ACQUISITION")
    cost_recorded = bool(settled) and any(cost["category"] == "ACQUISITION"
                                         for proof in settled for cost in proof["costs"])
    contribution = sum(proof["fixture_contribution_minor"] for proof in settled)
    target = plan["request"]["stop_after_visits"]
    evaluation = "REVIEW_EVIDENCE"
    if not pending and len(visits) >= target and (not retained or contribution <= 0):
        evaluation = "RECOMMEND_PAUSE"
    elif not pending and retained and contribution > 0:
        evaluation = "REVIEW_POSITIVE_FIXTURE"
    result = {
        "campaign_id": campaign_id, "scope": scope, "plan_sha256": plan["sha256"],
        "basis": "SETTLED_ACQUISITION_FIXTURE_ONLY", "visits": len(visits),
        "settled_captures": captured, "positive_net_orders": retained, "unresolved_orders": pending,
        "settled_conversion_bp": captured * 10000 // len(visits) if visits else None,
        "retained_net_order_conversion_bp": retained * 10000 // len(visits) if visits else None,
        "contribution_minor": contribution if settled and not pending else None,
        "recorded_order_acquisition_cost_minor": acquisition_cost if cost_recorded else None,
        "recommendation": evaluation, "currency": "CAD",
        "order_proofs": [{"id": proof["order_id"], "sha256": proof["sha256"]} for proof in settled],
        "verified_commercial_revenue": False, "external_action_authorized": False,
    }
    return {**result, "sha256": artifact_digest("acquisition_fixture_result", str(campaign_id), result)}


def observe_scoped_acquisition(db, scope):
    schemas = inspect(db.connection())
    if not all(schemas.has_table(model.__tablename__) for model in (
        FoundryCampaignVisit, FoundryRehearsalOrder, LegacyOrchestrationEvent,
    )):
        return []
    visit = FoundryCampaignVisit
    campaigns = db.scalars(select(visit.campaign_id).where(visit.scope_key == outcome_scope_key(scope))
                           .distinct().order_by(visit.campaign_id).limit(5)).all()
    results = []
    for campaign_id in campaigns:
        try:
            if read_plan(db, campaign_id, scope) is not None:
                results.append(settled_campaign(db, campaign_id, scope))
        except HTTPException as exc:
            if exc.status_code not in {404, 409}:
                raise
            results.append({"campaign_id": campaign_id, "scope": scope, "basis": "EVIDENCE_HOLD",
                            "verified_commercial_revenue": False, "external_action_authorized": False})
    return results
