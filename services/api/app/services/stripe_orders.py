"""Bind exact existing Foundry product evidence to a separately created Stripe intent."""
import os
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, field_validator
from sqlalchemy import inspect, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.stripe_finance import _event_receipt, stripe_id


class OrderBindingIn(StrictModel):
    order_id: UUID
    action_id: str = Field(pattern=r"^bfd_[a-f0-9]{32}$")
    payment_intent_id: str
    scope: MarketScope

    @field_validator("payment_intent_id")
    @classmethod
    def native_reference(cls, value):
        if not stripe_id(value, "pi"):
            raise ValueError("A native Stripe intent identity is required")
        return value


def _require_configured_mode(live):
    if os.getenv("VALHALLA_STRIPE_EVENT_MODE") != ("live" if live else "test"):
        raise HTTPException(503, "Stripe order evidence lane is disabled")
    expected_account = os.getenv("VALHALLA_STRIPE_ACCOUNT_ID")
    if not stripe_id(expected_account, "acct"):
        raise HTTPException(503, "Stripe account binding is unavailable")
    return expected_account


def _require_tables(db):
    inspector = inspect(db.connection())
    if not all(inspector.has_table(model.__tablename__) for model in (
        StripeOrderBinding, StripeBalanceEvidence, StripeFinancialEvent,
    )):
        raise HTTPException(503, "Stripe order evidence schema unavailable")


def _snapshot(row):
    value = row.binding
    if (not isinstance(value, dict) or value.get("payment_intent_id") != row.payment_intent_id
            or value.get("livemode") is not row.livemode or value.get("order_id") != str(row.id)
            or artifact_digest("stripe_order_binding", str(row.id), value) != row.binding_sha256):
        raise HTTPException(409, "Stripe order binding failed integrity")
    return value


def register_binding(db: Session, request: OrderBindingIn, *, live: bool):
    from app.routers.foundry_checkout import _listing

    account_id = _require_configured_mode(live)
    _require_tables(db)
    prior = db.get(StripeOrderBinding, request.order_id)
    if prior is not None:
        value = _snapshot(prior)
        if (value.get("action_id"), value.get("scope"), prior.payment_intent_id, prior.livemode,
                value.get("stripe_account_id")) != (
                request.action_id, request.scope.model_dump(), request.payment_intent_id, live, account_id):
            raise HTTPException(409, "Stripe order identity already has a different binding")
        return {**value, "sha256": prior.binding_sha256}
    receipt, product, amount, scope = _listing(db, request.action_id)
    if scope != request.scope.model_dump():
        raise HTTPException(409, "Stripe order scope differs from the approved Foundry listing")
    value = {"order_id": str(request.order_id), "scope": scope, "action_id": request.action_id,
             "stripe_account_id": account_id, "livemode": live, "payment_intent_id": request.payment_intent_id,
             "currency": "cad", "amount_minor": amount, "listing_sha256": receipt["sha256"],
             "product_id": product.product_id, "product_asset_id": str(product.id), "product_sha256": product.sha256,
             "basis": "OWNER_SCOPED_ORDER_BINDING", "payment_created": False}
    digest = artifact_digest("stripe_order_binding", str(request.order_id), value)
    db.add(StripeOrderBinding(id=request.order_id, livemode=live, payment_intent_id=request.payment_intent_id,
                              binding=value, binding_sha256=digest))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Stripe order or payment intent is already bound") from None
    return {**value, "sha256": digest}


def _refund_pending(db: Session, order: StripeOrderBinding, charge_id: str | None = None) -> bool:
    snapshot = StripeFinancialEvent.snapshot
    matches = snapshot["payment_intent_id"].as_string() == order.payment_intent_id
    if charge_id is not None:
        matches = or_(matches, snapshot["charge_id"].as_string() == charge_id)
    row = db.scalar(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == order.livemode, snapshot["kind"].as_string() == "charge.refunded", matches,
    ).limit(1))
    if row is None:
        return False
    _event_receipt(row, True)
    return True


def inspect_binding(db: Session, order_id: UUID, *, live: bool):
    account_id = _require_configured_mode(live)
    _require_tables(db)
    order = db.get(StripeOrderBinding, order_id)
    if order is None or order.livemode is not live:
        raise HTTPException(404, "Stripe order binding not found in the configured mode")
    value = _snapshot(order)
    if value["stripe_account_id"] != account_id:
        raise HTTPException(409, "Stripe order account differs from the configured account")
    balance = db.scalar(select(StripeBalanceEvidence).filter_by(
        payment_intent_id=order.payment_intent_id, livemode=live,
    ))
    projection = {"order": {**value, "sha256": order.binding_sha256}, "processor_evidence": None,
                  "status": "AWAITING_PROCESSOR_EVIDENCE", "bank_settlement_verified": False,
                  "available_cash_minor": None, "fulfillment_authorized": False, "entitlement_granted": False}
    if balance is None:
        if _refund_pending(db, order):
            projection["status"] = "REFUND_REVIEW_REQUIRED"
        return projection
    row = db.get(StripeFinancialEvent, balance.event_id)
    if row is None:
        raise HTTPException(409, "Stripe signed payment evidence is unavailable")
    _event_receipt(row, True)
    evidence = balance.evidence
    if (not isinstance(evidence, dict) or row.livemode is not live
            or balance.balance_transaction_id != evidence.get("balance_transaction_id")
            or balance.evidence_sha256 != artifact_digest("stripe_balance_evidence", balance.event_id, evidence)
            or evidence.get("event_snapshot_sha256") != row.snapshot_sha256
            or evidence.get("merchant_order_id") != str(order.id)
            or row.snapshot.get("merchant_order_id") != str(order.id)
            or (evidence.get("stripe_account_id"), evidence.get("payment_intent_id"),
                evidence.get("gross_minor"), evidence.get("currency")) != (
                    account_id, order.payment_intent_id, value["amount_minor"], value["currency"])):
        raise HTTPException(409, "Stripe processor and order evidence differ")
    if _refund_pending(db, order, evidence["charge_id"]):
        return {**projection, "status": "REFUND_REVIEW_REQUIRED"}
    return {**projection, "status": "MATCHED_PROCESSOR_EVIDENCE",
            "processor_evidence": {**evidence, "sha256": balance.evidence_sha256}}
