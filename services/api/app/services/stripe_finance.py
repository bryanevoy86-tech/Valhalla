"""Authenticate upstream deliveries, journal a minimal snapshot, and reconcile processor evidence."""
from contextlib import contextmanager
import hashlib
import os
import re
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import inspect, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding


def stripe_id(value, prefix):
    return (isinstance(value, str) and re.fullmatch(rf"{prefix}_[A-Za-z0-9_]{{1,120}}", value)
            is not None and not value.casefold().startswith((f"{prefix}_fixture_", f"{prefix}_sandbox")))


def minor_amount(value):
    return type(value) is int and 0 <= value <= 999_999_999_999


def merchant_order_reference(item):
    metadata = item.get("metadata")
    value = metadata.get("valhalla_order_id") if isinstance(metadata, dict) else None
    if value is None:
        return None
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, "Invalid Stripe merchant order reference") from None


def buyer_metadata(item):
    metadata = item.get("metadata")
    if not isinstance(metadata, dict) or not ({"valhalla_tenant_id", "valhalla_buyer_ref"} & metadata.keys()):
        return {}
    tenant, buyer = metadata.get("valhalla_tenant_id"), metadata.get("valhalla_buyer_ref")
    try:
        tenant = str(UUID(tenant))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, "Invalid Stripe tenant identity") from None
    if not isinstance(buyer, str) or not re.fullmatch("[a-f0-9]{64}", buyer):
        raise HTTPException(422, "Invalid Stripe buyer reference")
    return {"tenant_id": tenant, "buyer_ref": buyer}


def event_snapshot(payload, live):
    kind = payload["type"]
    data = payload.get("data")
    item = data.get("object") if isinstance(data, dict) else None
    if (payload.get("livemode") is not live or payload.get("account") or payload.get("context")
            or not stripe_id(payload.get("id"), "evt") or not isinstance(item, dict)
            or ("livemode" in item and item["livemode"] is not live)):
        raise HTTPException(422, "Unsupported Stripe account, mode or event identity")
    if kind.startswith("payment_intent."):
        object_type, prefix, intent = "payment_intent", "pi", item.get("id")
        amount = item.get("amount_received") if kind.endswith(".succeeded") else item.get("amount")
        charge = item.get("latest_charge")
        if kind == "payment_intent.succeeded" and (item.get("status") != "succeeded"
                or not minor_amount(amount) or amount <= 0 or not stripe_id(charge, "ch")):
            raise HTTPException(422, "Stripe capture snapshot is incomplete")
    elif kind == "charge.refunded":
        object_type, prefix, intent = "charge", "ch", item.get("payment_intent")
        amount, charge = item.get("amount_refunded"), item.get("id")
    elif kind == "charge.dispute.created":
        object_type, prefix, intent = "dispute", "dp", item.get("payment_intent")
        amount, charge = item.get("amount"), item.get("charge")
        if not stripe_id(charge, "ch"):
            raise HTTPException(422, "Stripe dispute charge identity is required")
    elif kind in {"payout.failed", "payout.canceled"}:
        object_type, prefix, intent = "payout", "po", None
        amount, charge = item.get("amount"), None
    else:
        object_type, prefix, intent = "checkout.session", "cs", item.get("payment_intent")
        amount, charge = item.get("amount_total"), None
    currency = item.get("currency")
    if (item.get("object") != object_type or not stripe_id(item.get("id"), prefix)
            or (intent is not None and not stripe_id(intent, "pi"))
            or (charge is not None and not stripe_id(charge, "ch"))
            or not isinstance(currency, str) or not re.fullmatch("[a-z]{3}", currency)
            or not minor_amount(amount)):
        raise HTTPException(422, "Unsupported Stripe financial object")
    snapshot = {"kind": kind, "livemode": live, "object_id": item["id"], "payment_intent_id": intent,
            "charge_id": charge, "amount_minor": amount, "currency": currency,
            "merchant_order_id": merchant_order_reference(item) if object_type == "payment_intent" else None}
    if object_type == "payment_intent" and item.get("customer") is not None:
        if not stripe_id(item["customer"], "cus"):
            raise HTTPException(422, "Unsupported Stripe customer identity")
        snapshot["stripe_customer_id"] = item["customer"]
    if object_type == "payment_intent":
        snapshot.update(buyer_metadata(item))
    return snapshot


def _event_receipt(row, duplicate):
    if (not isinstance(row.snapshot, dict) or row.snapshot.get("livemode") is not row.livemode
            or row.snapshot_sha256 != artifact_digest("stripe_event_snapshot", row.event_id, row.snapshot)):
        raise HTTPException(409, "Stripe event journal integrity check failed")
    return {"event_id": row.event_id, "status": "journaled", "duplicate": duplicate,
            "basis": "SIGNED_STRIPE_LIVE" if row.livemode else "SIGNED_STRIPE_TEST",
            "verified_financial_effect": False}


def journal_event(db: Session, payload, raw, live):
    snapshot = event_snapshot(payload, live)
    if not inspect(db.connection()).has_table(StripeFinancialEvent.__tablename__):
        raise HTTPException(503, "Stripe event journal unavailable")
    event_id = payload["id"]
    body_hash = hashlib.sha256(raw).hexdigest()
    if snapshot["kind"] in {"charge.refunded", "charge.dispute.created"} and inspect(db.connection()).has_table(
        StripeOrderBinding.__tablename__,
    ):
        captures = StripeFinancialEvent.snapshot
        matches = select(captures["payment_intent_id"].as_string()).where(
            StripeFinancialEvent.livemode == live,
            captures["kind"].as_string() == "payment_intent.succeeded",
            captures["charge_id"].as_string() == snapshot["charge_id"],
        )
        db.scalars(select(StripeOrderBinding).where(
            StripeOrderBinding.livemode == live,
            or_(StripeOrderBinding.payment_intent_id == snapshot["payment_intent_id"],
                StripeOrderBinding.payment_intent_id.in_(matches)),
        ).order_by(StripeOrderBinding.id).with_for_update()).all()
    previous = db.get(StripeFinancialEvent, event_id)
    if previous is None:
        row = StripeFinancialEvent(event_id=event_id, livemode=live, snapshot=snapshot, payload_sha256=body_hash,
                                   snapshot_sha256=artifact_digest("stripe_event_snapshot", event_id, snapshot))
        db.add(row)
        try:
            db.commit()
            return _event_receipt(row, False)
        except IntegrityError:
            db.rollback()
            previous = db.get(StripeFinancialEvent, event_id)
    if previous is None or (previous.payload_sha256, previous.livemode) != (body_hash, live):
        raise HTTPException(409, "Stripe event identity already has different evidence")
    return _event_receipt(previous, True)


def persist_delivery(payload, raw, live):
    from app.core.db import SessionLocal

    with SessionLocal() as db:
        return journal_event(db, payload, raw, live)


def provider_json(client, path, *, params=None):
    try:
        response = client.get(path, params=params)
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, "Stripe readback unavailable") from None
    if not isinstance(result, dict):
        raise HTTPException(409, "Stripe readback response is not an object")
    return result


def _provider_object(client, path, identity, kind):
    result = provider_json(client, path)
    if result.get("id") != identity or result.get("object") != kind:
        raise HTTPException(409, "Stripe readback identity mismatch")
    return result


def read_captured_charge(client: httpx.Client, account_id, snapshot):
    if snapshot["kind"] != "payment_intent.succeeded":
        raise HTTPException(409, "Independent readback only supports a successful capture")
    charge_id = snapshot["charge_id"]
    if not stripe_id(account_id, "acct") or not stripe_id(charge_id, "ch"):
        raise HTTPException(409, "Stripe account or capture identity is missing")
    _provider_object(client, "/v1/account", account_id, "account")
    charge = _provider_object(client, f"/v1/charges/{charge_id}", charge_id, "charge")
    gross, currency = snapshot["amount_minor"], snapshot["currency"]
    if (charge.get("livemode") is not snapshot["livemode"]
            or charge.get("payment_intent") != snapshot["payment_intent_id"] or charge.get("currency") != currency
            or not minor_amount(charge.get("amount_captured")) or charge["amount_captured"] != gross
            or charge.get("status") != "succeeded" or charge.get("paid") is not True
            or charge.get("captured") is not True or charge.get("refunded") is not False
            or charge.get("disputed") is not False or charge.get("amount_refunded") != 0):
        raise HTTPException(409, "Stripe charge is unmatched, refunded, disputed or missing balance evidence")
    order_reference = snapshot.get("merchant_order_id")
    if order_reference is not None and merchant_order_reference(charge) != order_reference:
        raise HTTPException(409, "Stripe charge merchant order differs from signed evidence")
    if snapshot.get("stripe_customer_id") and charge.get("customer") != snapshot["stripe_customer_id"]:
        raise HTTPException(409, "Stripe charge customer differs from signed evidence")
    if snapshot.get("buyer_ref") and buyer_metadata(charge) != {
        "tenant_id": snapshot.get("tenant_id"), "buyer_ref": snapshot["buyer_ref"],
    }:
        raise HTTPException(409, "Stripe charge tenant or buyer differs from signed evidence")
    return charge


def capture_evidence(client: httpx.Client, account_id, snapshot, now: datetime):
    charge = read_captured_charge(client, account_id, snapshot)
    charge_id, transaction_id = charge["id"], charge.get("balance_transaction")
    gross, currency = snapshot["amount_minor"], snapshot["currency"]
    order_reference = snapshot.get("merchant_order_id")
    if not stripe_id(transaction_id, "txn"):
        raise HTTPException(409, "Stripe charge lacks processor balance evidence")
    transaction = _provider_object(client, f"/v1/balance_transactions/{transaction_id}", transaction_id,
                                   "balance_transaction")
    fee, net, available = transaction.get("fee"), transaction.get("net"), transaction.get("available_on")
    if (transaction.get("source") != charge_id or transaction.get("currency") != currency
            or transaction.get("type") not in {"charge", "payment"}
            or not minor_amount(transaction.get("amount")) or transaction["amount"] != gross
            or not minor_amount(fee) or not minor_amount(net) or gross - fee != net
            or transaction.get("status") != "available" or type(available) is not int
            or not 0 < available <= int(now.timestamp())):
        raise HTTPException(409, "Stripe balance evidence is pending or does not match the capture")
    return {"stripe_account_id": account_id, "payment_intent_id": snapshot["payment_intent_id"],
            "charge_id": charge_id, "balance_transaction_id": transaction_id, "currency": currency,
            "merchant_order_id": order_reference,
            "gross_minor": gross, "fee_minor": fee, "net_minor": net, "available_on": available,
            "basis": "STRIPE_LIVE_PROCESSOR_BALANCE" if snapshot["livemode"] else "STRIPE_TEST_PROCESSOR_BALANCE",
            "bank_settlement_verified": False, "ledger_posting_created": False, "entitlement_granted": False}


def read_processor_balance(db: Session, event_id: str, *, client: httpx.Client, account_id: str, live: bool):
    if not stripe_id(event_id, "evt"):
        raise HTTPException(422, "Invalid Stripe event identity")
    inspector = inspect(db.connection())
    if not all(inspector.has_table(table) for table in (
        StripeFinancialEvent.__tablename__, StripeBalanceEvidence.__tablename__,
    )):
        raise HTTPException(503, "Stripe readback journal unavailable")
    event = db.get(StripeFinancialEvent, event_id, with_for_update=True)
    if event is None or event.livemode is not live:
        raise HTTPException(404, "Stripe event not found in the configured mode")
    _event_receipt(event, True)
    evidence = capture_evidence(client, account_id, event.snapshot, datetime.now(timezone.utc))
    evidence["event_snapshot_sha256"] = event.snapshot_sha256
    digest = artifact_digest("stripe_balance_evidence", event_id, evidence)
    prior = db.get(StripeBalanceEvidence, event_id)
    if prior is not None:
        if prior.evidence != evidence or prior.evidence_sha256 != digest:
            raise HTTPException(409, "Stored processor evidence differs from current Stripe readback")
        return {**evidence, "sha256": digest}
    db.add(StripeBalanceEvidence(event_id=event_id, livemode=live, payment_intent_id=evidence["payment_intent_id"],
                                 balance_transaction_id=evidence["balance_transaction_id"], evidence=evidence,
                                 evidence_sha256=digest))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Stripe capture or balance transaction already has a receipt") from None
    return {**evidence, "sha256": digest}


@contextmanager
def stripe_readback_client(*, live: bool):
    mode = "live" if live else "test"
    account_id = os.getenv("VALHALLA_STRIPE_ACCOUNT_ID")
    key = os.getenv("VALHALLA_STRIPE_READBACK_KEY", "")
    if (os.getenv("VALHALLA_STRIPE_EVENT_MODE") != mode
            or os.getenv("VALHALLA_STRIPE_READBACK_ENABLED") != "1"
            or not stripe_id(account_id, "acct") or not key.startswith(f"rk_{mode}_")):
        raise HTTPException(503, "Stripe restricted readback is disabled or unconfigured")
    with httpx.Client(base_url="https://api.stripe.com", auth=(key, ""), follow_redirects=False,
                      timeout=5.0, trust_env=False) as client:
        yield client, account_id


def configured_readback(db: Session, event_id: str, *, live: bool):
    with stripe_readback_client(live=live) as (client, account_id):
        return read_processor_balance(db, event_id, client=client, account_id=account_id, live=live)
