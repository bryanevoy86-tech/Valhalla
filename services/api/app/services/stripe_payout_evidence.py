"""Read processor payout membership without changing funds or claiming a bank posting."""
from datetime import datetime, timezone
import os
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding
from app.services.prime_business_execution import _event, _json
from app.services.stripe_finance import _provider_object, capture_evidence, minor_amount, provider_json, stripe_id, stripe_readback_client
from app.services.stripe_orders import _require_tables, inspect_binding


EVENT = "STRIPE_PROCESSOR_PAYOUT_MATCHED"


def payout_membership(client, payout_id, destination_id, evidence, *, live: bool):
    if not stripe_id(payout_id, "po") or not stripe_id(destination_id, "ba"):
        raise HTTPException(422, "A native Stripe payout and approved bank destination are required")
    payout = _provider_object(client, f"/v1/payouts/{payout_id}", payout_id, "payout")
    amount, arrival = payout.get("amount"), payout.get("arrival_date")
    if (payout.get("livemode") is not live or payout.get("automatic") is not True
            or payout.get("method") != "standard" or payout.get("type") != "bank_account"
            or payout.get("destination") != destination_id or payout.get("status") != "paid"
            or payout.get("reconciliation_status") != "completed" or payout.get("reversed_by")
            or payout.get("original_payout") or payout.get("failure_balance_transaction")
            or payout.get("failure_code") or payout.get("currency") != evidence["currency"]
            or not minor_amount(amount) or amount <= 0 or type(arrival) is not int or arrival <= 0):
        raise HTTPException(409, "Stripe payout is pending, reversed or outside the configured destination")
    found = provider_json(client, "/v1/balance_transactions", params={
        "payout": payout_id, "source": evidence["charge_id"], "limit": 2,
    })
    items = found.get("data")
    if (found.get("object") != "list" or found.get("has_more") is not False
            or not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict)):
        raise HTTPException(409, "Stripe payout membership for this capture is missing or ambiguous")
    member = items[0]
    expected = {"id": evidence["balance_transaction_id"], "object": "balance_transaction",
                "source": evidence["charge_id"], "currency": evidence["currency"], "status": "available",
                "amount": evidence["gross_minor"], "fee": evidence["fee_minor"], "net": evidence["net_minor"]}
    if (any(not minor_amount(member.get(key)) for key in ("amount", "fee", "net"))
            or any(member.get(key) != expected_value for key, expected_value in expected.items())):
        raise HTTPException(409, "Stripe payout member differs from the independently matched capture")
    return {"payout_id": payout_id, "processor_reported_payout_minor": amount, "processor_arrival_on": arrival,
            "destination_matches_configuration": True}


def record_payout_evidence(db: Session, order_id: UUID, payout_id: str, *, client, account_id: str,
                           destination_id: str, live: bool):
    _require_tables(db)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Payout evidence journal unavailable")
    order = db.get(StripeOrderBinding, order_id, with_for_update=True)
    if order is None or order.livemode is not live:
        raise HTTPException(404, "Stripe order not found in the configured mode")
    projection = inspect_binding(db, order_id, live=live)
    if projection["status"] != "MATCHED_PROCESSOR_EVIDENCE":
        raise HTTPException(409, "Current matched order and processor evidence are required")
    evidence = projection["processor_evidence"]
    if evidence["stripe_account_id"] != account_id:
        raise HTTPException(409, "Stripe account differs from the scoped order")
    recorded = db.scalar(select(StripeBalanceEvidence).filter_by(
        payment_intent_id=order.payment_intent_id, livemode=live,
    ))
    event = db.get(StripeFinancialEvent, recorded.event_id) if recorded is not None else None
    if event is None or event.snapshot_sha256 != evidence["event_snapshot_sha256"]:
        raise HTTPException(409, "Signed Stripe capture event differs from matched balance evidence")
    capture = capture_evidence(client, account_id, event.snapshot, datetime.now(timezone.utc))
    if any(evidence.get(key) != value for key, value in capture.items()):
        raise HTTPException(409, "Current Stripe capture differs from recorded processor evidence")
    match = payout_membership(client, payout_id, destination_id, capture, live=live)
    scope = projection["order"]["scope"]
    value = {
        "order_id": str(order_id), "order_sha256": order.binding_sha256, "scope": scope,
        "balance_evidence_sha256": evidence["sha256"], "currency": evidence["currency"],
        "capture_net_minor": evidence["net_minor"], **match,
        "basis": "STRIPE_LIVE_PAYOUT_MEMBERSHIP" if live else "STRIPE_TEST_PAYOUT_MEMBERSHIP",
        "bank_settlement_verified": False, "confirmed_bank_amount_minor": None, "ledger_posting_created": False,
    }
    reference = "STRIPE-PAYOUT-" + artifact_digest("stripe_order_payout_key", str(order_id), {"livemode": live})[:40]
    receipt = {**value, "sha256": artifact_digest("stripe_order_payout", reference, value)}
    prior = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=reference))
    if prior is not None:
        if (prior.event_type != EVENT or prior.legacy_instance_id != scope["legacy_instance_id"]
                or _json(prior.payload_json, {}) != receipt):
            raise HTTPException(409, "Stripe order payout already has different evidence")
        return receipt
    _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=EVENT,
           message="Stripe processor payout contains the exact order capture", payload=receipt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent Stripe payout evidence; replay the exact readback") from None
    return receipt


def configured_payout_readback(db: Session, order_id: UUID, payout_id: str, *, live: bool):
    destination_id = os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID")
    if not stripe_id(destination_id, "ba"):
        raise HTTPException(503, "Stripe payout destination is unconfigured")
    with stripe_readback_client(live=live) as (client, account_id):
        return record_payout_evidence(db, order_id, payout_id, client=client, account_id=account_id,
                                      destination_id=destination_id, live=live)
