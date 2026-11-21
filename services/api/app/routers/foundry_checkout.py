"""Rehearse Product Foundry capture, fulfillment and refunds with signed fixtures."""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.completion_registry import LegacyInstanceWorkItem
from app.models.foundry_checkout import FoundryRehearsalOrder, FoundryRehearsalPayment
from app.providers.stripe_adapter import verify_stripe_signature
from app.services.prime_business_execution import _check_legacy, _json, action_status, require_owner_mandate_key
from app.services.product_artifacts import load_artifact, verify_artifact


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


def _listing(db, action_id):
    state = action_status(db, action_id)
    receipt = state["receipt"]
    asset = receipt.get("product_asset") if receipt else None
    if not state["internal_artifact_verified"] or not isinstance(asset, dict):
        raise HTTPException(409, "A verified internal listing with product bytes is required")
    item = db.scalar(select(LegacyInstanceWorkItem).where(LegacyInstanceWorkItem.action_id == action_id))
    scope = {key: getattr(item, key) for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
    _check_legacy(db, **scope)
    data = _json(item.payload_json, {})
    artifact = load_artifact(db, UUID(asset["artifact_id"]), lock=True)
    verify_artifact(artifact)
    if (asset["sha256"] != artifact.sha256 or any(getattr(artifact, key) != value for key, value in scope.items())
            or data.get("product_id") != artifact.product_id or data.get("currency") != "CAD"):
        raise HTTPException(409, "Listing and product no longer match")
    return receipt, artifact, data["price_cents_cad"]


def _view(db, row):
    captured, refunded = db.execute(select(
        func.coalesce(func.sum(FoundryRehearsalPayment.captured_delta), 0),
        func.coalesce(func.sum(FoundryRehearsalPayment.refunded_delta), 0),
    ).where(FoundryRehearsalPayment.order_id == row.id)).one()
    if (captured, refunded) != (row.captured_minor, row.refunded_minor):
        raise HTTPException(409, "Rehearsal journal does not reconcile")
    return {
        "order_id": row.id, "currency": "CAD", "price_minor": row.amount_minor,
        "basis": "SIGNED_LOCAL_FIXTURE", "captured_minor": captured, "refunded_minor": refunded,
        "net_minor": captured - refunded, "internal_delivery_recorded": row.delivered_at is not None,
        "verified_commercial_revenue": False, "external_delivery_authorized": False,
    }


@router.post("/orders", status_code=201, dependencies=owner)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    previous = db.get(FoundryRehearsalOrder, payload.order_id, with_for_update=True)
    if previous is not None:
        if (previous.action_id, previous.payment_reference) != (payload.action_id, payload.payment_reference):
            raise HTTPException(409, "Rehearsal order ID already used")
        return _view(db, previous)
    receipt, artifact, amount = _listing(db, payload.action_id)
    order = FoundryRehearsalOrder(id=payload.order_id, action_id=payload.action_id, listing_sha256=receipt["sha256"],
                                  artifact_id=artifact.id, artifact_sha256=artifact.sha256,
                                  amount_minor=amount, payment_reference=payload.payment_reference)
    db.add(order)
    try:
        db.flush()
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
    receipt, artifact, price = _listing(db, order.action_id)
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
