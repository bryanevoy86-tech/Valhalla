"""Rehearse Product Foundry capture, fulfillment and refunds with signed fixtures."""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.foundry_checkout import FoundryCampaignVisit, FoundryFixtureSettlement, FoundryRehearsalOrder, FoundryRehearsalPayment
from app.models.treasury_reconciliation import StatementEntry, StatementImport
from app.models.marketing import MarketingCampaign
from app.providers.stripe_adapter import verify_stripe_signature
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
    _check_legacy(db, **scope)
    require_no_containment(db, scope)
    data = _json(item.payload_json, {})
    artifact = load_artifact(db, UUID(asset["artifact_id"]), lock=True)
    verify_artifact(artifact)
    if (asset["sha256"] != artifact.sha256 or any(getattr(artifact, key) != value for key, value in scope.items())
            or data.get("product_id") != artifact.product_id or data.get("currency") != "CAD"):
        raise HTTPException(409, "Listing and product no longer match")
    return receipt, artifact, data["price_cents_cad"], scope


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
    db.commit()
    return result


def _view(db, row):
    captured, refunded = db.execute(select(
        func.coalesce(func.sum(FoundryRehearsalPayment.captured_delta), 0),
        func.coalesce(func.sum(FoundryRehearsalPayment.refunded_delta), 0),
    ).where(FoundryRehearsalPayment.order_id == row.id)).one()
    if (captured, refunded) != (row.captured_minor, row.refunded_minor):
        raise HTTPException(409, "Rehearsal journal does not reconcile")
    costs = _rehearsal_costs(db, row)
    expense = sum(item["amount_minor"] for item in costs)
    return {
        "order_id": row.id, "currency": "CAD", "price_minor": row.amount_minor,
        "basis": "SIGNED_LOCAL_FIXTURE", "captured_minor": captured, "refunded_minor": refunded,
        "fixture_cost_minor": expense, "fixture_cost_count": len(costs),
        "fixture_contribution_minor": captured - refunded - expense if costs else None,
        "actual_profit_minor": None,
        "net_minor": captured - refunded, "internal_delivery_recorded": row.delivered_at is not None,
        "verified_commercial_revenue": False, "external_delivery_authorized": False,
    }


@router.post("/orders", status_code=201, dependencies=owner)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
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
    order = FoundryRehearsalOrder(id=payload.order_id, action_id=payload.action_id, listing_sha256=receipt["sha256"],
                                  artifact_id=artifact.id, artifact_sha256=artifact.sha256,
                                  amount_minor=amount, payment_reference=payload.payment_reference)
    db.add(order)
    try:
        db.flush()
        if visit is not None:
            visit.order_id = order.id
        result = _view(db, order)
        db.commit()
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
    order = db.get(FoundryRehearsalOrder, order_id, with_for_update=True)
    if order is None:
        raise HTTPException(404, "Rehearsal order not found")
    if order.captured_minor != order.amount_minor or order.refunded_minor:
        raise HTTPException(409, "An intact signed capture fixture is required")
    receipt, artifact, price, _ = _listing(db, order.action_id)
    if (receipt["sha256"], artifact.id, artifact.sha256, price) != (
        order.listing_sha256, order.artifact_id, order.artifact_sha256, order.amount_minor,
    ):
        raise HTTPException(409, "Product evidence changed")
    if order.delivered_at is None:
        order.delivered_at = datetime.now(timezone.utc)
    result = _view(db, order)
    db.commit()
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
        listing, asset, price, _ = _listing(db, order.action_id)
        if (listing["sha256"], asset.id, asset.sha256, price) != (
            order.listing_sha256, order.artifact_id, order.artifact_sha256, order.amount_minor,
        ):
            raise HTTPException(409, "Checkout evidence changed before capture")
        captured = amount
        order.captured_minor = amount
    else:
        if not order.refunded_minor <= amount <= order.captured_minor:
            raise HTTPException(409, "Fixture refund is out of sequence or exceeds capture")
        refunded = amount - order.refunded_minor
        order.refunded_minor = amount
    db.add(FoundryRehearsalPayment(event_id=event_id, order_id=order.id, sha256=digest,
                                  captured_delta=captured, refunded_delta=refunded))
    try:
        db.flush()
        result = _view(db, order)
        db.commit()
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


def _attribution_schema(db):
    tables = inspect(db.connection())
    if any(not tables.has_table(model.__tablename__) for model in (FoundryCampaignVisit, MarketingCampaign)):
        raise HTTPException(503, "Rehearsal attribution schema unavailable")


@router.post("/campaign-visits", status_code=201, dependencies=owner)
def record_campaign_visit(payload: VisitIn, db: Session = Depends(get_db)):
    _attribution_schema(db)
    scope = payload.model_dump(exclude={"visit_id", "campaign_id"})
    _check_legacy(db, **scope)
    if db.get(MarketingCampaign, payload.campaign_id) is None:
        raise HTTPException(404, "Campaign record not found")
    key = outcome_scope_key(scope)
    visit = db.get(FoundryCampaignVisit, payload.visit_id)
    if visit is not None:
        if (visit.campaign_id, visit.scope_key) != (payload.campaign_id, key):
            raise HTTPException(409, "Visit ID already used")
    else:
        db.add(FoundryCampaignVisit(id=payload.visit_id, campaign_id=payload.campaign_id, scope_key=key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Visit ID already used") from None
    return {"visit_id": payload.visit_id, "campaign_id": payload.campaign_id, "basis": "REHEARSED_VISIT"}


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
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Statement posting or signed payment already reconciled") from None
    return {**detail, "status": "MATCHED_FIXTURE"}
