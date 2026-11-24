"""Rehearse Product Foundry capture, fulfillment and refunds with signed fixtures."""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.heimdall.authority import is_live
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.foundry_checkout import FoundryCampaignVisit, FoundryFixtureSettlement, FoundryRehearsalOrder, FoundryRehearsalPayment
from app.models.treasury_reconciliation import StatementEntry, StatementImport
from app.models.marketing import MarketingCampaign
from app.providers.stripe_adapter import verify_stripe_signature
from app.schemas.market_intelligence import MarketScope
from app.services.acquisition_rehearsal import (
    AcquisitionPlanIn, CONSENT_TYPE, CUSTOMER_TYPE, EVENT_TYPE as ACQUISITION_PLAN_EVENT,
    SUPPRESSION_TYPE, consent_event_id, consent_receipt, customer_reference, journal_event,
    make_plan, plan_reference, read_plan, settled_campaign, verify_consent,
)
from app.services.acquisition_comparison import (
    ComparisonIn, REVIEWED_EVENT, REVIEWED_PREFIX, ReviewedComparisonIn, compare_campaigns,
    comparison_review_artifact, reviewed_capital_projection,
)
from app.services.acquisition_channel_fixture import ChannelIntentIn, ChannelReceiptIn, accept_channel_receipt, stage_channel
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, _json, action_status, require_owner_mandate_key
from app.services.product_artifacts import load_artifact, verify_artifact
from app.services.specialist_triggers import outcome_scope_key
from app.services.treasury_reconciliation import payload_for, statement_ready


def schema(db: Session = Depends(get_db)):
    inspector = inspect(db.connection())
    if any(not inspector.has_table(model.__tablename__) for model in (FoundryRehearsalOrder, FoundryRehearsalPayment)):
        raise HTTPException(503, "Foundry checkout rehearsal schema unavailable")


router = APIRouter(prefix="/api/prime/foundry/rehearsal", tags=["foundry-checkout"],
                   dependencies=[Depends(require_prime_control_key), Depends(schema)])
owner = [Depends(require_owner_mandate_key)]


class OrderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: UUID
    action_id: str = Field(pattern=r"^bfd_[a-f0-9]{32}$")
    payment_reference: str = Field(pattern=r"^pi_fixture_[a-zA-Z0-9_]{3,80}$")
    visit_id: UUID | None = None


def _listing(db, action_id):
    if _emergency_stop_active(db):
        raise HTTPException(503, "Checkout rehearsal paused by emergency stop")
    state = action_status(db, action_id)
    receipt = state["receipt"]
    asset = receipt.get("product_asset") if receipt else None
    if not state["internal_artifact_verified"] or not isinstance(asset, dict):
        raise HTTPException(409, "A verified internal listing with product bytes is required")
    item = db.scalar(select(LegacyInstanceWorkItem).where(LegacyInstanceWorkItem.action_id == action_id))
    scope = {key: getattr(item, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    _check_legacy(db, **scope, lock=True)
    require_no_containment(db, scope)
    data = _json(item.payload_json, {})
    artifact = load_artifact(db, UUID(asset["artifact_id"]), lock=True)
    verify_artifact(artifact)
    if (asset["sha256"] != artifact.sha256 or any(getattr(artifact, key) != value for key, value in scope.items())
            or data.get("product_id") != artifact.product_id or data.get("currency") != "CAD"):
        raise HTTPException(409, "Listing and product no longer match")
    return receipt, artifact, data["price_cents_cad"], scope


def _verify_order_listing(db, order):
    receipt, artifact, price, _ = _listing(db, order.action_id)
    if (receipt["sha256"], artifact.id, artifact.sha256, price) != (
        order.listing_sha256, order.artifact_id, order.artifact_sha256, order.amount_minor,
    ):
        raise HTTPException(409, "Product evidence changed")


COST_EVENT = "FOUNDRY_ORDER_COST_FIXTURE"


class CostIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    fixture_ref: str = Field(min_length=4, max_length=80, pattern=r"^fixture:[a-zA-Z0-9_-]+$")
    category: Literal["ACQUISITION", "PAYMENT_FEE", "FULFILLMENT", "SUPPORT"]
    amount_minor: int = Field(strict=True, gt=0, le=100_000_000)


def _rehearsal_costs(db, order):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return []
    prefix = f"FOUNDRY-COST-{order.id}-"
    records = db.scalars(select(LegacyOrchestrationEvent).where(
        LegacyOrchestrationEvent.event_type == COST_EVENT,
        LegacyOrchestrationEvent.event_id.startswith(prefix),
    ).order_by(LegacyOrchestrationEvent.id).limit(51)).all()
    if len(records) > 50:
        raise HTTPException(409, "Rehearsal cost count exceeds the scope limit")
    items = []
    for record in records:
        payload = _json(record.payload_json, {})
        checksum = payload.pop("sha256", None)
        if payload.get("order_id") != str(order.id) or checksum != artifact_digest("foundry_cost", record.event_id, payload):
            raise HTTPException(409, "Rehearsal cost evidence failed integrity")
        items.append(payload)
    return items


@router.post("/orders/{order_id}/cost-fixtures", status_code=201, dependencies=owner)
def record_cost(order_id: UUID, request: CostIn, db: Session = Depends(get_db)):
    return _record_cost(order_id, request, db)


def _record_cost(order_id: UUID, request: CostIn, db: Session, *, commit=True):
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    # Reconcile expense evidence against the historical order even during containment.
    work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order.action_id))
    if work is None:
        raise HTTPException(409, "Rehearsal order scope unavailable")
    scope = {key: getattr(work, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    _check_legacy(db, **scope)
    costs = _rehearsal_costs(db, order)
    ref = request.fixture_ref.casefold()
    payload = {**request.model_dump(), "fixture_ref": ref, "order_id": str(order_id), "currency": "CAD"}
    for recorded in costs:
        if recorded["fixture_ref"] == ref:
            if recorded != payload:
                raise HTTPException(409, "Rehearsal cost reference already used")
            return _view(db, order)
    if len(costs) >= 50:
        raise HTTPException(409, "Rehearsal cost limit reached")
    event_id = f"FOUNDRY-COST-{order.id}-" + hashlib.sha256(ref.encode()).hexdigest()[:24]
    payload["sha256"] = artifact_digest("foundry_cost", event_id, payload)
    _event(db, event_id=event_id, legacy_instance_id=work.legacy_instance_id, event_type=COST_EVENT,
           message="Private rehearsal expense fixture recorded", payload=payload)
    db.flush()
    result = _view(db, order)
    db.commit() if commit else db.flush()
    return result


SUPPORT_EVENT = "FOUNDRY_REFUND_SUPPORT_RESOLVED"


class SupportResolutionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_refunded_minor: int = Field(strict=True, gt=0, le=10_000_000)
    resolution: str = Field(min_length=10, max_length=500)


def _support_event_id(row):
    return f"FOUNDRY-SUPPORT-{row.id}-{row.refunded_minor}"


def _support_resolution(db, order):
    if not order.refunded_minor:
        return None
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return None
    event_id = _support_event_id(order)
    event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id))
    if event is None:
        return None
    payload = _json(event.payload_json, None)
    if not isinstance(payload, dict):
        raise HTTPException(409, "Support resolution payload is unavailable")
    legacy_id = db.scalar(select(LegacyInstanceWorkItem.legacy_instance_id).filter_by(action_id=order.action_id))
    checksum = payload.pop("sha256", None)
    if (event.event_type != SUPPORT_EVENT or legacy_id is None or event.legacy_instance_id != legacy_id
            or payload.get("evidence_scope") != "INTERNAL_REHEARSAL_ONLY"
            or payload.get("order_id") != str(order.id)
            or payload.get("action_id") != order.action_id
            or payload.get("refunded_minor") != order.refunded_minor
            or payload.get("listing_sha256") != order.listing_sha256
            or payload.get("artifact_sha256") != order.artifact_sha256
            or checksum != artifact_digest("foundry_support", event_id, payload)):
        raise HTTPException(409, "Support resolution evidence failed integrity")
    return {"event_id": event_id, "refunded_minor": order.refunded_minor,
            "status": "RESOLVED_INTERNAL_REHEARSAL", "external_customer_action_verified": False}


@router.post("/orders/{order_id}/support-resolution", dependencies=owner)
def resolve_refund_support(order_id: UUID, payload: SupportResolutionIn, db: Session = Depends(get_db)):
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    if order.refunded_minor != payload.expected_refunded_minor:
        raise HTTPException(409, "A reconciled refund at the reviewed total is required")
    return _record_support_resolution(db, order, payload.resolution)


def _record_support_resolution(
    db: Session, order: FoundryRehearsalOrder, resolution: str, *, routine_scope: dict | None = None, commit=True,
):
    work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order.action_id))
    if work is None:
        raise HTTPException(409, "Rehearsal order scope unavailable")
    scope = {key: getattr(work, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    if routine_scope is not None and scope != routine_scope:
        raise HTTPException(404, "Rehearsal order not found in this scope")
    _check_legacy(db, **scope)
    result = _view(db, order)
    if routine_scope is not None:
        require_no_containment(db, scope)
        exception = result["fulfillment_exception"]
        if (result["checkout_state"] != "REFUNDED" or order.captured_minor != order.amount_minor
                or (exception and exception["status"] == "HELD")):
            raise HTTPException(409, "Support exception requires a scoped representative")
    event_id = _support_event_id(order)
    if result["support_resolution"] is not None:
        event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id))
        if routine_scope is None and _json(event.payload_json, {}).get("resolution") != resolution:
            raise HTTPException(409, "The reviewed refund already has a different support resolution")
        return result
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Foundry support evidence schema unavailable")
    evidence = {
        "order_id": str(order.id), "action_id": order.action_id, "refunded_minor": order.refunded_minor,
        "listing_sha256": order.listing_sha256, "artifact_sha256": order.artifact_sha256,
        "resolution": resolution, "evidence_scope": "INTERNAL_REHEARSAL_ONLY",
    }
    message = "Owner recorded support resolution for reconciled rehearsal refund"
    if routine_scope is not None:
        evidence["resolution_actor"] = "PRIME_ROUTINE_FIXTURE"
        message = "Prime recorded routine support resolution for reconciled rehearsal refund"
    evidence["sha256"] = artifact_digest("foundry_support", event_id, evidence)
    _event(db, event_id=event_id, legacy_instance_id=work.legacy_instance_id, event_type=SUPPORT_EVENT,
           message=message, payload=evidence)
    db.flush()
    result = _view(db, order)
    db.commit() if commit else db.flush()
    return result


@router.post("/orders/{order_id}/routine-support")
def reconcile_routine_refund_support(order_id: UUID, scope: MarketScope, db: Session = Depends(get_db)):
    if (is_live() or os.getenv("VALHALLA_ROUTINE_SUPPORT_REHEARSAL") != "1"
            or os.getenv("APP_ENV", "").lower() not in {"dev", "test", "sandbox"}
            or os.getenv("ENV", "").lower() not in {"", "dev", "test", "sandbox"}):
        raise HTTPException(503, "Routine support rehearsal disabled")
    if _emergency_stop_active(db):
        raise HTTPException(503, "Routine support rehearsal stopped")
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    return _record_support_resolution(
        db, order, "Reconciled full signed refund in the disposable checkout.", routine_scope=scope.model_dump(),
    )


FULFILLMENT_EVENT = "FOUNDRY_FULFILLMENT_EXCEPTION"


class FulfillmentExceptionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    event_id: UUID
    previous_event_id: UUID | None = None
    action: Literal["HOLD", "RELEASE_FOR_RETRY"]
    reason: str = Field(min_length=10, max_length=500)


def _order_evidence(order):
    return {"order_id": str(order.id), "action_id": order.action_id, "listing_sha256": order.listing_sha256,
            "artifact_sha256": order.artifact_sha256}


def _fulfillment_exception(db, order):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return None
    event = db.scalar(select(LegacyOrchestrationEvent).where(
        LegacyOrchestrationEvent.event_type == FULFILLMENT_EVENT,
        LegacyOrchestrationEvent.event_id.startswith(f"FOUNDRY-FUL-{order.id.hex}-"),
    ).order_by(LegacyOrchestrationEvent.id.desc()).limit(1))
    if event is None:
        return None
    stored = _json(event.payload_json, None)
    if not isinstance(stored, dict):
        raise HTTPException(409, "Fulfillment exception evidence is unavailable")
    checksum = stored.pop("sha256", None)
    legacy_id = db.scalar(select(LegacyInstanceWorkItem.legacy_instance_id).filter_by(action_id=order.action_id))
    if (legacy_id is None or event.legacy_instance_id != legacy_id
            or any(stored.get(key) != value for key, value in _order_evidence(order).items())
            or stored.get("action") not in {"HOLD", "RELEASE_FOR_RETRY"}
            or checksum != artifact_digest("foundry_fulfillment_exception", event.event_id, stored)):
        raise HTTPException(409, "Fulfillment exception evidence failed integrity")
    if order.refunded_minor >= order.amount_minor:
        status = "CLOSED_BY_REFUND"
    else:
        status = "HELD" if stored["action"] == "HOLD" else "RETRY_REVIEWED"
    return {"event_id": stored["event_id"], "status": status, "basis": "INTERNAL_REHEARSAL_ONLY"}


@router.post("/orders/{order_id}/fulfillment-exception", dependencies=owner)
def review_fulfillment_exception(order_id: UUID, payload: FulfillmentExceptionIn, db: Session = Depends(get_db)):
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Foundry fulfillment evidence schema unavailable")
    work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order.action_id))
    if work is None:
        raise HTTPException(409, "Rehearsal order scope unavailable")
    _check_legacy(db, **{key: getattr(work, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")})
    current = _view(db, order)
    event_id = f"FOUNDRY-FUL-{order.id.hex}-{payload.event_id.hex}"
    evidence = {**_order_evidence(order), **payload.model_dump(mode="json")}
    evidence["sha256"] = artifact_digest("foundry_fulfillment_exception", event_id, evidence)
    earlier = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id))
    if earlier is not None:
        if (earlier.event_type != FULFILLMENT_EVENT or earlier.legacy_instance_id != work.legacy_instance_id
                or _json(earlier.payload_json, {}) != evidence):
            raise HTTPException(409, "Fulfillment event ID already used")
        return current
    state = current["fulfillment_exception"]
    prior_id = str(payload.previous_event_id) if payload.previous_event_id else None
    if prior_id != (state["event_id"] if state else None):
        raise HTTPException(409, "Review requires the current fulfillment exception receipt")
    if order.captured_minor != order.amount_minor or order.delivered_at is not None or order.refunded_minor >= order.amount_minor:
        raise HTTPException(409, "Only captured, undelivered orders with a balance can enter fulfillment review")
    if (payload.action == "RELEASE_FOR_RETRY") != bool(state and state["status"] == "HELD"):
        raise HTTPException(409, "Review must alternate hold and release transitions")
    if payload.action == "RELEASE_FOR_RETRY":
        if order.refunded_minor:
            raise HTTPException(409, "Partially refunded orders require refund support review")
        _verify_order_listing(db, order)
    _event(db, event_id=event_id, legacy_instance_id=work.legacy_instance_id, event_type=FULFILLMENT_EVENT,
           message="Owner reviewed a held fulfillment in the private rehearsal", payload=evidence)
    db.flush()
    result = _view(db, order)
    db.commit()
    return result


def _view(db, row):
    captured, refunded = db.execute(select(
        func.coalesce(func.sum(FoundryRehearsalPayment.captured_delta), 0),
        func.coalesce(func.sum(FoundryRehearsalPayment.refunded_delta), 0),
    ).where(FoundryRehearsalPayment.order_id == row.id)).one()
    if (captured, refunded) != (row.captured_minor, row.refunded_minor):
        raise HTTPException(409, "Rehearsal journal does not reconcile")
    if not 0 <= refunded <= captured <= row.amount_minor:
        raise HTTPException(409, "Rehearsal payment amounts are inconsistent")
    if refunded:
        checkout_state = "REFUNDED" if refunded == captured else "PARTIALLY_REFUNDED"
    elif row.delivered_at is not None:
        checkout_state = "DELIVERED_INTERNAL"
    else:
        checkout_state = "PAID_AWAITING_DELIVERY" if captured else "AWAITING_CAPTURE"
    costs = _rehearsal_costs(db, row)
    expense = sum(item["amount_minor"] for item in costs)
    support = _support_resolution(db, row)
    exception = _fulfillment_exception(db, row)
    return {
        "order_id": row.id, "currency": "CAD", "price_minor": row.amount_minor,
        "basis": "SIGNED_LOCAL_FIXTURE", "captured_minor": captured, "refunded_minor": refunded,
        "fixture_cost_minor": expense, "fixture_cost_count": len(costs),
        "fixture_contribution_minor": captured - refunded - expense if costs else None,
        "actual_profit_minor": None,
        "checkout_state": checkout_state,
        "owner_followup_required": bool(
            (refunded and support is None) or (exception and exception["status"] == "HELD")
        ),
        "support_resolution": support, "fulfillment_exception": exception,
        "net_minor": captured - refunded, "internal_delivery_recorded": row.delivered_at is not None,
        "verified_commercial_revenue": False, "external_delivery_authorized": False,
    }


def _require_current_campaign_plan(db: Session, campaign_id: int, plan: dict) -> None:
    recorded = AcquisitionPlanIn.model_validate(plan["request"])
    current = make_plan(db, campaign_id, recorded, datetime.now(timezone.utc).date())
    if (plan["demand_sha256"] != current["demand_sha256"]
            or plan.get("consumer_research") != current.get("consumer_research")):
        raise HTTPException(409, "Campaign demand evidence has changed")


@router.post("/orders", status_code=201, dependencies=owner)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    return _create_order(payload, db)


def _create_order(payload: OrderIn, db: Session, *, commit=True):
    previous = db.get(FoundryRehearsalOrder, payload.order_id, with_for_update=True)
    if previous is not None:
        if (previous.action_id, previous.payment_reference) != (payload.action_id, payload.payment_reference):
            raise HTTPException(409, "Rehearsal order ID already used")
        if inspect(db.connection()).has_table(FoundryCampaignVisit.__tablename__):
            recorded_visit = db.scalar(select(FoundryCampaignVisit.id).filter_by(order_id=previous.id))
            if recorded_visit != payload.visit_id:
                raise HTTPException(409, "Order already has different attribution")
        return _view(db, previous)
    receipt, artifact, amount, scope = _listing(db, payload.action_id)
    visit = None
    if payload.visit_id is not None:
        _attribution_schema(db)
        visit = db.get(FoundryCampaignVisit, payload.visit_id, with_for_update=True)
        if visit is None or visit.scope_key != outcome_scope_key(scope) or visit.order_id is not None:
            raise HTTPException(409, "Campaign visit is unavailable to this order scope")
        plan = read_plan(db, visit.campaign_id, scope)
        if plan is not None:
            _require_current_campaign_plan(db, visit.campaign_id, plan)
            if plan["request"]["channel"] == "DIRECT_OPT_IN":
                consent = verify_consent(
                    journal_event(db, consent_event_id(visit.id)), scope, visit.campaign_id, visit.id,
                )
                suppression_key, _ = customer_reference(scope, UUID(consent["consent_fixture_id"]))
                if journal_event(db, suppression_key) is not None:
                    raise HTTPException(409, "Synthetic customer opt-in was withdrawn before order attribution")
    order = FoundryRehearsalOrder(id=payload.order_id, action_id=payload.action_id, listing_sha256=receipt["sha256"],
                                  artifact_id=artifact.id, artifact_sha256=artifact.sha256,
                                  amount_minor=amount, payment_reference=payload.payment_reference)
    db.add(order)
    try:
        db.flush()
        if visit is not None:
            visit.order_id = order.id
        result = _view(db, order)
        db.commit() if commit else db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Order or payment reference already used") from None
    return result


@router.get("/orders/{order_id}")
def read_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    return _view(db, order)


@router.post("/orders/{order_id}/delivery", dependencies=owner)
def record_delivery(order_id: UUID, db: Session = Depends(get_db)):
    return _record_delivery(order_id, db)


def _record_delivery(order_id: UUID, db: Session, *, commit=True):
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    if order.captured_minor != order.amount_minor or order.refunded_minor:
        raise HTTPException(409, "An intact signed capture fixture is required")
    current = _view(db, order)
    if current["fulfillment_exception"] and current["fulfillment_exception"]["status"] == "HELD":
        raise HTTPException(409, "Fulfillment is held for owner review")
    _verify_order_listing(db, order)
    if order.delivered_at is None:
        order.delivered_at = datetime.now(timezone.utc)
    result = _view(db, order)
    db.commit() if commit else db.flush()
    return result


async def _signed_fixture(request: Request):
    secret = os.getenv("VALHALLA_FOUNDRY_FIXTURE_SECRET")
    if not secret or secret in {os.getenv("STRIPE_WEBHOOK_SECRET"), os.getenv("STRIPE_SECRET_KEY"),
                                os.getenv("VALHALLA_PRIME_CONTROL_KEY"), os.getenv("VALHALLA_OWNER_MANDATE_KEY")}:
        raise HTTPException(503, "Rehearsal fixture signing unavailable")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 32768:
            raise HTTPException(413, "Rehearsal fixture exceeds the byte limit")
        body.extend(chunk)
    raw = bytes(body)
    if not verify_stripe_signature(raw, request.headers.get("Stripe-Signature"), secret):
        raise HTTPException(400, "Fixture signature invalid")
    try:
        event = json.loads(raw)
        kind, event_id, data = event["type"], event["id"], event["data"]["object"]
        if (event.get("livemode") is not False or not re.fullmatch(r"evt_fixture_[a-zA-Z0-9_]{3,80}", event_id)
                or kind not in {"payment_intent.succeeded", "charge.refunded"} or data.get("currency") != "cad"):
            raise ValueError
        payment = data["id"] if kind == "payment_intent.succeeded" else data["payment_intent"]
        amount = data["amount_received"] if kind == "payment_intent.succeeded" else data["amount_refunded"]
        if not re.fullmatch(r"pi_fixture_[a-zA-Z0-9_]{3,80}", payment) or type(amount) is not int or amount <= 0:
            raise ValueError
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(422, "Invalid sandbox payment fixture") from None
    return kind, event_id, payment, amount, hashlib.sha256(raw).hexdigest()


@router.post("/payment-fixtures")
def apply_fixture(event: tuple = Depends(_signed_fixture), db: Session = Depends(get_db)):
    return _apply_fixture(event, db)


def _apply_fixture(event: tuple, db: Session, *, commit=True):
    kind, event_id, payment, amount, digest = event
    order = db.scalar(select(FoundryRehearsalOrder).filter_by(payment_reference=payment).with_for_update())
    if order is None:
        raise HTTPException(404, "Rehearsal payment reference not found")
    previous = db.get(FoundryRehearsalPayment, event_id)
    if previous is not None:
        if (previous.sha256, previous.order_id) != (digest, order.id):
            raise HTTPException(409, "Fixture event ID already used")
        return _view(db, order)
    _view(db, order)
    captured = refunded = 0
    if kind == "payment_intent.succeeded":
        if amount != order.amount_minor or order.captured_minor:
            raise HTTPException(409, "Fixture capture does not match the outstanding order amount")
        _verify_order_listing(db, order)
        captured = amount
        order.captured_minor = amount
    else:
        if not order.refunded_minor < amount <= order.captured_minor:
            raise HTTPException(409, "Fixture refund is out of sequence or exceeds capture")
        refunded = amount - order.refunded_minor
        order.refunded_minor = amount
    db.add(FoundryRehearsalPayment(event_id=event_id, order_id=order.id, sha256=digest,
                                  captured_delta=captured, refunded_delta=refunded))
    try:
        db.flush()
        result = _view(db, order)
        db.commit() if commit else db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Fixture event ID already used") from None
    return result


class CampaignScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    engine_id: str = Field(min_length=3, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=80)


class VisitIn(CampaignScope):
    visit_id: UUID
    campaign_id: int = Field(gt=0)
    consent_fixture_id: UUID | None = None


class SuppressionIn(CampaignScope):
    consent_fixture_id: UUID


def _attribution_schema(db):
    tables = inspect(db.connection())
    if any(not tables.has_table(model.__tablename__) for model in (FoundryCampaignVisit, MarketingCampaign)):
        raise HTTPException(503, "Rehearsal attribution schema unavailable")


@router.post("/campaign-visits", status_code=201, dependencies=owner)
def record_campaign_visit(payload: VisitIn, db: Session = Depends(get_db)):
    return _record_campaign_visit(payload, db)


def _record_campaign_visit(payload: VisitIn, db: Session, *, commit=True):
    _attribution_schema(db)
    scope = payload.model_dump(exclude={"visit_id", "campaign_id", "consent_fixture_id"})
    _check_legacy(db, **scope, lock=True)
    visit = db.get(FoundryCampaignVisit, payload.visit_id)
    if visit is None:
        require_no_containment(db, scope)
    if db.get(MarketingCampaign, payload.campaign_id, with_for_update=True) is None:
        raise HTTPException(404, "Campaign record not found")
    key = outcome_scope_key(scope)
    plan = read_plan(db, payload.campaign_id, scope)
    direct = plan is not None and plan["request"]["channel"] == "DIRECT_OPT_IN"
    if direct != (payload.consent_fixture_id is not None):
        raise HTTPException(409, "Direct acquisition visits require scoped synthetic opt-in evidence")
    if visit is not None:
        if (visit.campaign_id, visit.scope_key) != (payload.campaign_id, key):
            raise HTTPException(409, "Visit ID already used")
        if direct:
            event = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=consent_event_id(visit.id)))
            proof = verify_consent(event, scope, payload.campaign_id, visit.id)
            if proof["consent_fixture_id"] != str(payload.consent_fixture_id):
                raise HTTPException(409, "Visit ID already uses different opt-in evidence")
    else:
        if plan is not None:
            if _emergency_stop_active(db):
                raise HTTPException(503, "Campaign attribution paused by emergency stop")
            _require_current_campaign_plan(db, payload.campaign_id, plan)
            count = db.scalar(select(func.count()).select_from(FoundryCampaignVisit).filter_by(
                campaign_id=payload.campaign_id, scope_key=key,
            ))
            if count >= plan["request"]["stop_after_visits"]:
                raise HTTPException(409, "Campaign reached its approved fixture visit limit")
        if direct:
            suppress_key, _ = customer_reference(scope, payload.consent_fixture_id)
            if journal_event(db, suppress_key) is not None:
                raise HTTPException(409, "Synthetic customer is suppressed for this scope")
            customer_key, customer = customer_reference(scope, payload.consent_fixture_id, payload.campaign_id)
            if journal_event(db, customer_key) is not None:
                raise HTTPException(409, "Synthetic customer is already attributed to this campaign")
            _event(db, event_id=customer_key, legacy_instance_id=scope["legacy_instance_id"],
                   event_type=CUSTOMER_TYPE, message="Synthetic customer attribution registered", payload=customer)
            proof = consent_receipt(scope, payload.campaign_id, payload.visit_id, payload.consent_fixture_id)
            _event(db, event_id=consent_event_id(payload.visit_id), legacy_instance_id=scope["legacy_instance_id"],
                   event_type=CONSENT_TYPE, message="Synthetic scoped opt-in recorded", payload=proof)
        db.add(FoundryCampaignVisit(id=payload.visit_id, campaign_id=payload.campaign_id, scope_key=key))
        try:
            db.commit() if commit else db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Visit ID already used") from None
    return {"visit_id": payload.visit_id, "campaign_id": payload.campaign_id, "basis": "REHEARSED_VISIT"}


@router.post("/consent-suppressions", status_code=201, dependencies=owner)
def suppress_consent(payload: SuppressionIn, db: Session = Depends(get_db)):
    scope = payload.model_dump(exclude={"consent_fixture_id"})
    _check_legacy(db, **scope, lock=True)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Synthetic consent journal unavailable")
    ref, evidence = customer_reference(scope, payload.consent_fixture_id)
    prior = journal_event(db, ref)
    if prior is not None:
        if (prior.event_type != SUPPRESSION_TYPE or prior.legacy_instance_id != scope["legacy_instance_id"]
                or _json(prior.payload_json, {}) != evidence):
            raise HTTPException(409, "Synthetic suppression integrity mismatch")
    else:
        _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"],
               event_type=SUPPRESSION_TYPE, message="Synthetic customer suppressed", payload=evidence)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Concurrent suppression already recorded; retry the same request") from None
    return {"status": "SUPPRESSED_IN_FIXTURE", "sha256": evidence["sha256"],
            "external_outreach_authorized": False}


@router.post("/campaign-comparisons")
def compare_acquisition_campaigns(payload: ComparisonIn, db: Session = Depends(get_db)):
    _attribution_schema(db)
    _check_legacy(db, **payload.scope.model_dump())
    return compare_campaigns(db, payload)


@router.post("/channel-intents", status_code=201, dependencies=owner)
def stage_channel_intent(payload: ChannelIntentIn, db: Session = Depends(get_db)):
    return stage_channel(db, payload)


@router.post("/channel-fixture-receipts", status_code=201)
def apply_channel_fixture_receipt(
    payload: ChannelReceiptIn, db: Session = Depends(get_db),
    signature: str | None = Header(default=None, alias="X-Acquisition-Fixture-Signature"),
):
    return accept_channel_receipt(db, payload, signature)


@router.post("/campaign-comparisons/review-artifact", dependencies=owner)
def review_acquisition_comparison(payload: ComparisonIn, db: Session = Depends(get_db)):
    return comparison_review_artifact(compare_acquisition_campaigns(payload, db))


@router.post("/campaign-comparisons/reviewed", status_code=201, dependencies=owner)
def record_reviewed_comparison(payload: ReviewedComparisonIn, db: Session = Depends(get_db)):
    _attribution_schema(db)
    scope = payload.scope.model_dump()
    _check_legacy(db, **scope)
    value = reviewed_capital_projection(db, payload)
    reference = REVIEWED_PREFIX + value["sha256"]
    prior = journal_event(db, reference)
    if prior is not None:
        if (prior.legacy_instance_id != scope["legacy_instance_id"] or prior.event_type != REVIEWED_EVENT
                or _json(prior.payload_json, {}) != value):
            raise HTTPException(409, "Reviewed acquisition receipt integrity mismatch")
        return value
    _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=REVIEWED_EVENT,
           message="Independently reviewed acquisition and capital fixture", payload=value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent review already recorded; retry the exact request") from None
    return value


@router.post("/campaigns/{campaign_id}/acquisition-plan", status_code=201, dependencies=owner)
def record_acquisition_plan(campaign_id: int, payload: AcquisitionPlanIn, db: Session = Depends(get_db)):
    return _record_acquisition_plan(campaign_id, payload, db)


def _record_acquisition_plan(campaign_id: int, payload: AcquisitionPlanIn, db: Session, *, durable=True):
    _attribution_schema(db)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Campaign plan journal unavailable")
    scope = payload.scope.model_dump()
    _check_legacy(db, **scope, lock=True)
    if _emergency_stop_active(db):
        raise HTTPException(503, "Campaign planning paused by emergency stop")
    require_no_containment(db, scope)
    if db.get(MarketingCampaign, campaign_id, with_for_update=True) is None:
        raise HTTPException(404, "Campaign record not found")
    result = make_plan(db, campaign_id, payload, datetime.now(timezone.utc).date())
    ref = plan_reference(campaign_id)
    result["sha256"] = artifact_digest("acquisition_fixture_plan", ref, result)
    prior = read_plan(db, campaign_id, scope)
    if prior is not None:
        if prior != result:
            raise HTTPException(409, "Campaign already has a different acquisition plan")
        return prior
    if db.scalar(select(FoundryCampaignVisit.id).filter_by(campaign_id=campaign_id).limit(1)) is not None:
        raise HTTPException(409, "Register an acquisition plan before its first visit")
    _event(db, event_id=ref, legacy_instance_id=scope["legacy_instance_id"], event_type=ACQUISITION_PLAN_EVENT,
           message="Demand-backed acquisition rehearsal planned", payload=result)
    try:
        db.commit() if durable else db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent campaign plan already recorded") from None
    return result


@router.post("/campaigns/{campaign_id}/settled-review")
def settled_acquisition_review(campaign_id: int, scope: CampaignScope, db: Session = Depends(get_db)):
    _attribution_schema(db)
    values = scope.model_dump()
    _check_legacy(db, **values)
    return settled_campaign(db, campaign_id, values)


@router.post("/campaigns/{campaign_id}/summary")
def campaign_summary(campaign_id: int, scope: CampaignScope, db: Session = Depends(get_db)):
    _attribution_schema(db)
    values = scope.model_dump()
    _check_legacy(db, **values)
    visit, order = FoundryCampaignVisit, FoundryRehearsalOrder
    scoped = select(visit.id).where(visit.campaign_id == campaign_id, visit.scope_key == outcome_scope_key(values))
    total = db.scalar(select(func.count()).select_from(scoped.subquery()))
    paid = db.scalars(select(order).join(visit, visit.order_id == order.id).where(
        visit.id.in_(scoped), order.captured_minor > 0,
    ).order_by(order.id).with_for_update(of=order)).all()
    totals = [_view(db, row) for row in paid]
    return {
        "campaign_id": campaign_id, "basis": "SIGNED_LOCAL_FIXTURE", "rehearsed_visits": total,
        "rehearsed_conversions": len(totals), "currency": "CAD",
        "rehearsed_net_minor": sum(item["net_minor"] for item in totals),
        "rehearsed_recorded_cost_minor": sum(item["fixture_cost_minor"] for item in totals),
        "rehearsed_contribution_minor": (sum(item["fixture_contribution_minor"] for item in totals)
                                         if totals and all(item["fixture_cost_count"] for item in totals) else None),
        "actual_profit_minor": None, "verified_commercial_revenue": False,
    }

class SettlementIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    statement_id: UUID
    entry_ref: str = Field(min_length=3, max_length=180)
    payment_event_id: str = Field(pattern=r"^evt_fixture_[a-zA-Z0-9_]{3,80}$")


@router.post("/orders/{order_id}/settlement-fixtures", dependencies=owner)
def reconcile_settlement(order_id: UUID, request: SettlementIn, db: Session = Depends(get_db)):
    return _reconcile_settlement(order_id, request, db)


def _reconcile_settlement(order_id: UUID, request: SettlementIn, db: Session, *, commit=True):
    if not statement_ready(db) or not inspect(db.connection()).has_table(FoundryFixtureSettlement.__tablename__):
        raise HTTPException(503, "Rehearsal settlement schema unavailable")
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    payment = db.get(FoundryRehearsalPayment, request.payment_event_id)
    if order is None or payment is None or payment.order_id != order_id:
        raise HTTPException(404, "Signed payment event not found for order")
    _view(db, order)
    work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order.action_id))
    if work is None:
        raise HTTPException(409, "Rehearsal order scope unavailable")
    scope = {key: getattr(work, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    _check_legacy(db, **scope)
    statement = db.get(StatementImport, request.statement_id)
    if statement is None:
        raise HTTPException(404, "Statement fixture not found")
    document = payload_for(statement)
    if document.scope.model_dump() != scope or document.purpose != "BUSINESS" or document.currency != "CAD":
        raise HTTPException(409, "Statement scope, purpose or currency does not match the order")
    entry_ref = request.entry_ref.casefold()
    entry = next((item for item in document.entries if item.external_ref.casefold() == entry_ref), None)
    key = artifact_digest("statement_transaction", statement.account_key, entry_ref)
    indexed = db.get(StatementEntry, key)
    if entry is None or indexed is None or indexed.statement_id != statement.id or entry.category != "TRANSFER":
        raise HTTPException(409, "An indexed settlement transfer entry is required")
    amount = payment.captured_delta - payment.refunded_delta
    detail = {"order_id": order_id, "payment_event_id": payment.event_id, "statement_id": statement.id,
              "payment_sha256": payment.sha256, "statement_sha256": statement.digest,
              "expected_minor": amount, "statement_minor": entry.amount_minor,
              "difference_minor": entry.amount_minor - amount, "currency": document.currency,
              "basis": "RECONCILIATION_FIXTURE", "actual_settlement_verified": False}
    previous = db.get(FoundryFixtureSettlement, payment.event_id)
    if previous is not None and (previous.statement_entry_key, previous.statement_id, previous.statement_sha256,
                                 previous.payment_sha256, previous.amount_minor) != (
        key, statement.id, statement.digest, payment.sha256, amount,
    ):
        raise HTTPException(409, "Payment already reconciled to different fixture evidence")
    if amount != entry.amount_minor:
        return {**detail, "status": "DISCREPANCY"}
    if previous is None:
        db.add(FoundryFixtureSettlement(payment_event_id=payment.event_id, statement_entry_key=key,
                                        statement_id=statement.id, statement_sha256=statement.digest,
                                        payment_sha256=payment.sha256, amount_minor=amount))
        try:
            db.commit() if commit else db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Statement posting or signed payment already reconciled") from None
    return {**detail, "status": "MATCHED_FIXTURE"}


def scoped_checkout_learning(db: Session, scope: dict, outcomes: list[dict], *, artifact_id=None, order_id=None) -> list[dict]:
    """Re-read checkout fixtures tied to a verified scoped listing outcome."""
    inspector = inspect(db.connection())
    if not outcomes or any(not inspector.has_table(model.__tablename__) for model in (
        FoundryRehearsalOrder, FoundryRehearsalPayment,
    )):
        return []
    has_settlements = inspector.has_table(FoundryFixtureSettlement.__tablename__)
    has_statements = all(inspector.has_table(model.__tablename__) for model in (StatementImport, StatementEntry))
    by_action = {item["action_id"]: item for item in outcomes if item.get("product_asset")
                 and (artifact_id is None or item["product_asset"]["artifact_id"] == artifact_id)}
    if not by_action:
        return []
    query = select(FoundryRehearsalOrder).where(
        FoundryRehearsalOrder.action_id.in_(by_action),
    )
    if order_id is not None:
        query = query.where(FoundryRehearsalOrder.id == order_id)
    orders = db.scalars(query.order_by(FoundryRehearsalOrder.id).limit(20)).all()
    observations = []
    for order in orders:
        outcome = by_action[order.action_id]
        asset = outcome["product_asset"]
        reference = {"order_id": str(order.id), "outcome_event_id": outcome["outcome_event_id"],
                     "basis": "LOCAL_CHECKOUT_REHEARSAL", "verified_commercial_revenue": False}
        try:
            if (order.listing_sha256, str(order.artifact_id), order.artifact_sha256) != (
                outcome["artifact_sha256"], asset["artifact_id"], asset["sha256"],
            ):
                raise HTTPException(409, "Checkout listing differs from verified outcome")
            view = _view(db, order)
            payments = db.scalars(select(FoundryRehearsalPayment).where(
                FoundryRehearsalPayment.order_id == order.id,
            ).order_by(FoundryRehearsalPayment.event_id).limit(101)).all()
            if len(payments) > 100:
                raise HTTPException(409, "Checkout payment history exceeds advisory limit")
            matched, pending, settlement_refs = [], [], []
            for payment in payments:
                settlement = db.get(FoundryFixtureSettlement, payment.event_id) if has_settlements else None
                if settlement is None:
                    pending.append(payment.event_id)
                    continue
                if not has_statements:
                    raise HTTPException(409, "Checkout settlement evidence storage is unavailable")
                statement = db.get(StatementImport, settlement.statement_id)
                indexed = db.get(StatementEntry, settlement.statement_entry_key)
                if (statement is None or indexed is None or indexed.statement_id != statement.id
                        or settlement.statement_sha256 != statement.digest or settlement.payment_sha256 != payment.sha256
                        or settlement.amount_minor != payment.captured_delta - payment.refunded_delta):
                    raise HTTPException(409, "Checkout settlement linkage failed integrity")
                document = payload_for(statement)
                matched_entry = next((entry for entry in document.entries
                                      if entry.category == "TRANSFER" and entry.amount_minor == settlement.amount_minor
                                      and artifact_digest("statement_transaction", statement.account_key,
                                                          entry.external_ref.casefold()) == indexed.key), None)
                if (document.scope.model_dump() != scope or document.purpose != "BUSINESS" or document.currency != "CAD"
                        or matched_entry is None):
                    raise HTTPException(409, "Checkout settlement no longer matches the statement fixture")
                matched.append(payment.event_id)
                settlement_refs.append({"payment_event_id": payment.event_id, "payment_sha256": payment.sha256,
                                        "statement_id": str(statement.id), "statement_sha256": statement.digest,
                                        "statement_entry_key": indexed.key, "amount_minor": settlement.amount_minor,
                                        "posted_on": matched_entry.posted_on.isoformat()})
            observations.append({**view, **reference, "matched_fixture_payment_ids": matched, "unmatched_fixture_payment_ids": pending,
                                 "status": "MATCHED_FIXTURE" if matched and not pending else "UNRECONCILED_FIXTURE"})
            if order_id is not None:
                observations[-1]["settlements"] = settlement_refs
                observations[-1]["costs"] = _rehearsal_costs(db, order)
        except HTTPException:
            observations.append({**reference, "status": "EVIDENCE_CONFLICT"})
    return observations


def closed_checkout_proof(db: Session, order_id: UUID, *, scope=None, lock=False) -> dict:
    from app.services.prime_business_execution import _mimir_outcome_id, verified_internal_outcomes

    schema(db)
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=lock)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order.action_id))
    if work is None:
        raise HTTPException(409, "Checkout listing work is unavailable")
    exact_scope = {key: getattr(work, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    if scope is not None and exact_scope != scope:
        raise HTTPException(409, "Checkout scope differs from the economic operation")
    outcomes = verified_internal_outcomes(db, **exact_scope, limit=0, trigger_event_id=_mimir_outcome_id(work.action_id))
    observations = scoped_checkout_learning(db, exact_scope, outcomes, order_id=order_id)
    observation = observations[0] if observations else {}
    if (observation.get("status") != "MATCHED_FIXTURE" or not observation["internal_delivery_recorded"]
            or observation["captured_minor"] != observation["price_minor"] or observation["owner_followup_required"]
            or observation["fixture_cost_count"] == 0):
        raise HTTPException(409, "Current closed checkout, settlement, delivery and cost evidence is required")
    data = jsonable_encoder({"scope": exact_scope, "listing_sha256": order.listing_sha256,
                            "product_sha256": order.artifact_sha256, "delivered_at": order.delivered_at,
                            **observation})
    return {**data, "sha256": artifact_digest("foundry_closed_checkout_fixture", str(order_id), data)}


@router.get("/orders/{order_id}/closed-checkout-proof")
def read_closed_checkout_proof(order_id: UUID, db: Session = Depends(get_db)):
    return closed_checkout_proof(db, order_id)
