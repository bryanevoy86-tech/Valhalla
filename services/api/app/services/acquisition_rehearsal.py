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
from app.services.consumer_evidence import read_consumer_evidence
from app.services.prime_business_execution import _json
from app.services.specialist_triggers import outcome_scope_key


EVENT_TYPE = "ACQUISITION_FIXTURE_PLAN"
CONSENT_TYPE = "ACQUISITION_FIXTURE_OPT_IN"


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
    research = read_consumer_evidence(db, row, evidence, scope, today)
    return {
        "campaign_id": campaign_id, "request": request.model_dump(mode="json"), "demand_sha256": row.digest,
        "target_buyer_segment": demand["buyer_segment"], "source_id": demand["source_id"],
        "demand_sample_count": demand["sample_count"], "demand_positive_count": demand["demand_count"],
        "unit_economics": economics(evidence), "basis": "INTERNAL_ACQUISITION_REHEARSAL",
        **({"consumer_research": research} if research is not None else {}),
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
    if not isinstance(plan, dict) or not isinstance(plan.get("request"), dict):
        raise HTTPException(409, "Campaign plan integrity or scope mismatch")
    digest = plan.pop("sha256", None)
    if (event.event_type != EVENT_TYPE or event.legacy_instance_id != scope["legacy_instance_id"]
            or plan.get("request", {}).get("scope") != scope
            or digest != artifact_digest("acquisition_fixture_plan", ref, plan)):
        raise HTTPException(409, "Campaign plan integrity or scope mismatch")
    return {**plan, "sha256": digest}


def consent_event_id(visit_id):
    return f"ACQ-OPTIN-{visit_id}"


def consent_receipt(scope, campaign_id, visit_id, consent_id):
    body = {"scope": scope, "campaign_id": campaign_id, "visit_id": str(visit_id),
            "consent_fixture_id": str(consent_id), "basis": "EXPLICIT_OPT_IN_FIXTURE",
            "external_outreach_authorized": False}
    return {**body, "sha256": artifact_digest("acquisition_fixture_consent", consent_event_id(visit_id), body)}


def verify_consent(event, scope, campaign_id, visit_id):
    body = _json(event.payload_json, {}) if event else {}
    try:
        consent_id = UUID(body["consent_fixture_id"])
        if (event.event_type != CONSENT_TYPE or event.legacy_instance_id != scope["legacy_instance_id"]
                or body != consent_receipt(scope, campaign_id, visit_id, consent_id)):
            raise ValueError
    except (KeyError, ValueError, TypeError, AttributeError):
        raise HTTPException(409, "Direct acquisition visit lacks matching synthetic consent") from None
    return body


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
    consent_digests = []
    if plan["request"]["channel"] == "DIRECT_OPT_IN":
        for start in range(0, len(visits), 200):
            page = visits[start:start + 200]
            ids = [consent_event_id(item.id) for item in page]
            receipts = {row.event_id: row for row in db.scalars(select(LegacyOrchestrationEvent).where(
                LegacyOrchestrationEvent.event_id.in_(ids),
            ))}
            consent_digests.extend(verify_consent(receipts.get(ref), scope, campaign_id, item.id)["sha256"]
                                   for ref, item in zip(ids, page))
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
    budget_exceeded = cost_recorded and acquisition_cost > plan["request"]["experiment_budget_minor"]
    if budget_exceeded or (not pending and len(visits) >= target and (not retained or contribution <= 0)):
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
        "acquisition_cost_per_positive_net_order_minor": acquisition_cost // retained
        if not pending and cost_recorded and retained else None,
        "recorded_acquisition_cost_exceeds_budget": budget_exceeded,
        "recommendation": evaluation, "currency": "CAD",
        "order_proofs": [{"id": proof["order_id"], "sha256": proof["sha256"]} for proof in settled],
        "consent_receipt_count": len(consent_digests),
        "consent_evidence_sha256": artifact_digest("acquisition_fixture_consent_set", str(campaign_id),
                                                   {"receipts": consent_digests}) if consent_digests else None,
        "verified_commercial_revenue": False, "external_action_authorized": False,
    }
    if plan.get("consumer_research") is not None:
        result["research_relationship"] = {
            "consumer_research_sha256": plan["consumer_research"]["sha256"],
            "research_actions": plan["consumer_research"]["research_actions"],
            "campaign_causality_verified": False,
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
