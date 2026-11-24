"""One owner-authorized, test-only refund attempt and independent processor evidence."""
import os
import re
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import inspect, select, update
from sqlalchemy.exc import IntegrityError

from app.core.runtime_flags import is_sandbox
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyInstanceWorkItem, LegacyOrchestrationEvent as Event
from app.models.go_live_state import GoLiveState
from app.models.stripe_finance import StripeFinancialEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import _bound_prime_decision, _emergency_stop_active, _event, _json
from app.services.specialist_triggers import outcome_scope_key
from app.services.stripe_finance import (
    _event_receipt, _provider_object, provider_json, read_captured_charge, stripe_id, stripe_readback_client,
)
from app.services.stripe_orders import inspect_binding
from app.services.stripe_refund_correction import refund_evidence

EVENT = "STRIPE_SANDBOX_REFUND_TRIAL"
WRITER_KEY = "VALHALLA_STRIPE_SANDBOX_REFUND_WRITE_KEY"


class SandboxRefundAuthority(StrictModel):
    scope: MarketScope
    charge_id: str = Field(pattern=r"^ch_[a-zA-Z0-9]{1,120}$")
    capture_event_id: str = Field(pattern=r"^evt_[a-zA-Z0-9]{1,120}$")
    amount_minor: int = Field(strict=True, ge=1, le=100_000)
    ttl_seconds: int = Field(strict=True, ge=60, le=3600)


def now():
    return datetime.now(timezone.utc)


def guard(db, *, dispatch=False):
    if (not is_sandbox() or os.getenv("APP_ENV") != "staging" or os.getenv("ENV") != "staging"
            or os.getenv("VALHALLA_STRIPE_EVENT_MODE") != "test"
            or os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_ENABLED") != "1"
            or any(os.getenv(name) for name in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
                                                "VALHALLA_STRIPE_BANK_BOOKING_SCOPE", "VALHALLA_STRIPE_DELIVERY_SCOPE"))
            or any(os.getenv(name, "").lower() not in {"", "0", "false", "off"} for name in (
                "VALHALLA_STRIPE_BANK_BOOKING_ENABLED", "VALHALLA_STRIPE_DELIVERY_ENABLED",
            ))
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:\.[a-z]+)?", os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION", ""))):
        raise HTTPException(503, "Sandbox refund commissioning is disabled")
    schema = inspect(db.connection())
    if not all(schema.has_table(model.__tablename__) for model in (Event, GoLiveState)):
        raise HTTPException(503, "Sandbox refund governance schema unavailable")
    release = db.get(GoLiveState, 1)
    if release is None or release.go_live_enabled or (dispatch and _emergency_stop_active(db)):
        raise HTTPException(503, "Sandbox refund operational hold")


def key(order_id, phase):
    return f"STR-TEST-RF-{order_id.hex}-{phase}"


def read(db, order_id, phase):
    ref = key(order_id, phase)
    row = db.scalar(select(Event).filter_by(event_id=ref))
    if row is None:
        return None
    body = _json(row.payload_json, {})
    digest = body.pop("sha256", None) if isinstance(body, dict) else None
    if (row.event_type != EVENT or digest is None or row.legacy_instance_id != body.get("scope", {}).get("legacy_instance_id")
            or digest != artifact_digest(EVENT, ref, body)):
        raise HTTPException(409, "Sandbox refund receipt failed integrity")
    return {**body, "sha256": digest}


def append(db, order_id, phase, scope, data):
    ref = key(order_id, phase)
    body = {**data, "scope": scope, "order_id": str(order_id), "livemode": False,
            "ledger_posting_created": False, "bank_settlement_verified": False, "available_cash_minor": None}
    body["sha256"] = artifact_digest(EVENT, ref, body)
    _event(db, event_id=ref, event_type=EVENT, legacy_instance_id=scope["legacy_instance_id"],
           message=f"Sandbox refund {phase}", payload=body)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Sandbox refund receipt already exists") from None
    return body


def capture(db, order_id, scope):
    view = inspect_binding(db, order_id, live=False, include_held_evidence=True)
    order, evidence = view["order"], view["processor_evidence"]
    if order["scope"] != scope or not evidence:
        raise HTTPException(409, "An exact independently checked test capture is required")
    return view, order, evidence


def prepare(db, order_id, request):
    guard(db, dispatch=True)
    scope = request.scope.model_dump()
    if os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE") != outcome_scope_key(scope):
        raise HTTPException(409, "Sandbox refund requires the authorized receiving scope")
    view, order, evidence = capture(db, order_id, scope)
    row = db.get(StripeFinancialEvent, request.capture_event_id)
    if (view["status"] != "MATCHED_PROCESSOR_EVIDENCE" or row is None
            or row.snapshot_sha256 != evidence["event_snapshot_sha256"]
            or request.charge_id != evidence["charge_id"] or request.amount_minor != order["amount_minor"]):
        raise HTTPException(409, "Sandbox authority requires the intact full capture")
    require_no_containment(db, scope)
    version = os.environ["VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION"]
    request_body = {"charge": request.charge_id, "amount": request.amount_minor,
                    "metadata[valhalla_refund_intent]": key(order_id, "intent")}
    data = {"binding_sha256": order["sha256"], "capture_sha256": evidence["sha256"],
            "capture_event_id": row.event_id, "stripe_account_id": order["stripe_account_id"],
            "request": request_body, "api_version": version, "ttl_seconds": request.ttl_seconds}
    prior = read(db, order_id, "intent")
    if prior is not None:
        if prior["scope"] != scope or any(prior.get(k) != v for k, v in data.items()):
            raise HTTPException(409, "Sandbox refund authority differs from the existing intent")
        return prior
    data["expires_at"] = int(now().timestamp()) + request.ttl_seconds
    data["request_sha256"] = artifact_digest("stripe_test_refund_request", key(order_id, "intent"), data)
    return append(db, order_id, "intent", scope, {**data, "status": "AUTHORIZED_TEST_INTENT"})


def lock_intent(db, order_id):
    db.execute(update(Event).where(Event.event_id == key(order_id, "intent")).values(message=Event.message))
    intent = read(db, order_id, "intent")
    if intent is None:
        raise HTTPException(404, "Sandbox refund intent not found")
    return intent


def dispatch(db, order_id: UUID, writer):
    guard(db, dispatch=True)
    intent = lock_intent(db, order_id)
    if read(db, order_id, "attempt"):
        db.rollback()
        return {"status": "READBACK_REQUIRED", "provider_write_attempted": False}
    scope = intent["scope"]
    if (now().timestamp() >= intent["expires_at"]
            or intent["api_version"] != os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION")
            or os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(409, "Sandbox refund authority expired or changed")
    view, order, evidence = capture(db, order_id, scope)
    require_no_containment(db, scope)
    from app.routers.foundry_checkout import _listing

    listing, _, _, actual_scope = _listing(db, order["action_id"])
    if (view["status"] != "MATCHED_PROCESSOR_EVIDENCE" or order["sha256"] != intent["binding_sha256"]
            or evidence["sha256"] != intent["capture_sha256"] or listing["sha256"] != order["listing_sha256"]
            or actual_scope != scope):
        raise HTTPException(409, "Sandbox capture, listing or scope changed")
    if listing.get("prime_decision"):
        work = db.scalar(select(LegacyInstanceWorkItem).filter_by(action_id=order["action_id"]))
        decision = listing["prime_decision"]
        if _bound_prime_decision(db, UUID(decision["verdict_id"]), work, _json(work.payload_json, {})) != decision:
            raise HTTPException(409, "Prime refund-source evidence changed")
    row = db.get(StripeFinancialEvent, intent["capture_event_id"])
    if row is None or row.snapshot_sha256 != evidence["event_snapshot_sha256"]:
        raise HTTPException(409, "Original signed sandbox capture changed")
    _event_receipt(row, True)
    read_captured_charge(writer, order["stripe_account_id"], row.snapshot)
    if _emergency_stop_active(db) or now().timestamp() >= intent["expires_at"]:
        raise HTTPException(409, "Sandbox refund held before dispatch")

    # Persist the only permitted attempt before I/O. A restarted worker only reads.
    attempt = append(db, order_id, "attempt", scope, {
        "intent_sha256": intent["sha256"], "request_sha256": intent["request_sha256"],
        "idempotency_key": f"valhalla-{intent['request_sha256']}", "started_at": int(now().timestamp()),
    })
    if _emergency_stop_active(db) or now().timestamp() >= intent["expires_at"]:
        return {"status": "READBACK_REQUIRED", "provider_write_attempted": False}
    try:
        response = writer.post("/v1/refunds", data=intent["request"], headers={
            "Idempotency-Key": attempt["idempotency_key"], "Stripe-Version": intent["api_version"],
        })
        response.raise_for_status()
        refund = response.json()
    except (httpx.HTTPError, ValueError):
        return {"status": "READBACK_REQUIRED", "provider_write_attempted": True}
    if not matches_intent(refund, intent):
        return {"status": "READBACK_REQUIRED", "provider_write_attempted": True}
    return append(db, order_id, "response", scope, {
        "status": "SUBMITTED_TEST_REFUND", "attempt_sha256": attempt["sha256"], "refund_id": refund["id"],
    })


def matches_intent(refund, intent):
    return (isinstance(refund, dict) and refund.get("object") == "refund" and stripe_id(refund.get("id"), "re")
            and refund.get("charge") == intent["request"]["charge"] and refund.get("amount") == intent["request"]["amount"]
            and refund.get("currency") == "cad" and refund.get("metadata") ==
            {"valhalla_refund_intent": intent["request"]["metadata[valhalla_refund_intent]"]})


def observe(db, order_id, reader, account_id):
    guard(db)
    intent = lock_intent(db, order_id)
    scope = intent["scope"]
    if os.getenv("VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE") != outcome_scope_key(scope):
        raise HTTPException(409, "Sandbox refund readback requires the original scope")
    attempt = read(db, order_id, "attempt")
    if not attempt or attempt["intent_sha256"] != intent["sha256"] or account_id != intent["stripe_account_id"]:
        raise HTTPException(409, "An exact sandbox dispatch attempt is required")
    _, order, capture_receipt = capture(db, order_id, scope)
    if (order["sha256"], capture_receipt["sha256"]) != (intent["binding_sha256"], intent["capture_sha256"]):
        raise HTTPException(409, "Sandbox capture binding changed")
    refund_list = provider_json(reader, "/v1/refunds", params={"charge": intent["request"]["charge"], "limit": 100})
    refunds = refund_list.get("data")
    if refund_list.get("has_more") is not False or not isinstance(refunds, list) or len(refunds) != 1:
        raise HTTPException(409, "Unique independent sandbox refund evidence is unavailable")
    refund = refunds[0]
    posted = read(db, order_id, "response")
    if not matches_intent(refund, intent) or (posted and (
        posted["refund_id"] != refund["id"] or posted["attempt_sha256"] != attempt["sha256"]
    )):
        raise HTTPException(409, "Sandbox refund is foreign to the authorized intent")
    refund_id = refund["id"]
    native = _provider_object(reader, f"/v1/refunds/{refund_id}", refund_id, "refund")
    if not matches_intent(native, intent):
        raise HTTPException(409, "Direct sandbox refund readback differs from the authorized intent")

    snapshot = StripeFinancialEvent.snapshot
    events = db.scalars(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode.is_(False), snapshot["kind"].as_string() == "charge.refunded",
        snapshot["charge_id"].as_string() == intent["request"]["charge"],
        snapshot["payment_intent_id"].as_string() == order["payment_intent_id"],
    ).limit(2)).all()
    if len(events) != 1:
        raise HTTPException(409, "Unique signed sandbox refund callback required")
    event = events[0]
    _event_receipt(event, True)
    received_at = event.received_at
    if received_at is None or int(received_at.replace(tzinfo=received_at.tzinfo or timezone.utc).timestamp()) < attempt["started_at"]:
        raise HTTPException(409, "Sandbox callback predates the dispatch attempt")
    evidence = refund_evidence(reader, account_id, order, event.snapshot, refund_id, now())
    data = {"status": "VERIFIED_SANDBOX_PROCESSOR_REFUND", "attempt_sha256": attempt["sha256"],
            "event_id": event.event_id, "event_sha256": event.payload_sha256, **evidence}
    prior = read(db, order_id, "verified")
    if prior:
        if any(prior.get(k) != v for k, v in data.items()):
            raise HTTPException(409, "Sandbox processor proof changed")
        return prior
    return append(db, order_id, "verified", scope, data)


def configured_observation(db, order_id):
    guard(db)
    with stripe_readback_client(live=False) as (reader, account_id):
        return observe(db, order_id, reader, account_id)


def configured_dispatch(db, order_id):
    guard(db, dispatch=True)
    writer_key = os.getenv(WRITER_KEY, "")
    if (not writer_key.startswith("rk_test_") or any(os.getenv(name) for name in (
        "VALHALLA_STRIPE_READBACK_KEY", "VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", "VALHALLA_LOKI_REVIEWER_KEY",
        "VALHALLA_PRIME_CONTROL_KEY", "VALHALLA_OWNER_MANDATE_KEY", "VALHALLA_FACTORY_KEY",
        "PLAID_SECRET", "VALHALLA_PLAID_READ_ACCESS_TOKEN",
    ))):
        raise HTTPException(503, "Refund writer requires its own restricted sandbox credential")
    with httpx.Client(base_url="https://api.stripe.com", auth=(writer_key, ""),
                      headers={"Stripe-Version": os.environ["VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION"]},
                      follow_redirects=False, trust_env=False, timeout=5) as writer:
        return dispatch(db, order_id, writer)
