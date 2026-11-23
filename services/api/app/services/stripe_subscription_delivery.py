"""Acknowledge exact completed service and release its matched CAD obligation."""
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.accounting.models import JournalEntry
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_recurring import StripePaidPeriod
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event
from app.services.stripe_bank_booking import invoice_bank_summary
from app.services.stripe_finance import stripe_id
from app.services.stripe_fulfillment import _read_record, _write_record
from app.services.stripe_recurring import _binding, _period_value, _reversed, _subscriber
from app.services.stripe_revenue_release import SOURCE, _release_posting

ACK = "STRIPE_RECURRING_SERVICE_ACKNOWLEDGED"
RELEASE = "STRIPE_RECURRING_LIABILITY_RELEASED"


class SubscriptionAckIn(StrictModel):
    paid_period_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SubscriptionReleaseIn(StrictModel):
    acknowledgment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _now():
    return datetime.now(timezone.utc)


def _exact_period(db, local_id, invoice_id, live, *, tenant_id: UUID | None = None, principal=None):
    if not stripe_id(invoice_id, "in"):
        raise HTTPException(422, "Native invoice identity required")
    row, binding, _ = _binding(db, local_id, live, lock=True)
    if principal is not None:
        _subscriber(db, binding, tenant_id, principal)
    period = db.get(StripePaidPeriod, invoice_id)
    if period is None or period.binding_id != local_id:
        raise HTTPException(404, "Exact paid service period unavailable")
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Service evidence journal unavailable")
    verified = _period_value(row, period)
    if _reversed(db, row, verified):
        raise HTTPException(409, "Paid service period requires correction review")
    now = _now()
    if period.period_end > int(now.timestamp()):
        raise HTTPException(409, "Service period has not ended")
    return binding, period, verified, now


def subscriber_service_history(db, tenant_id, local_id, principal, *, live):
    row, binding, _ = _binding(db, local_id, live)
    _subscriber(db, binding, tenant_id, principal)
    now = int(_now().timestamp())
    periods = db.scalars(select(StripePaidPeriod).where(
        StripePaidPeriod.binding_id == local_id, StripePaidPeriod.period_end <= now,
    ).order_by(StripePaidPeriod.period_end.desc()).limit(20)).all()
    result = []
    for period in periods:
        evidence = _period_value(row, period)
        if _reversed(db, row, evidence):
            continue
        result.append({"invoice_id": period.invoice_id, "period_start": period.period_start,
                       "period_end": period.period_end, "paid_period_sha256": period.evidence_sha256})
    return {"tenant_id": binding["tenant_id"], "subscription_id": local_id, "completed_paid_periods": result,
            "basis": "STRIPE_LIVE_SUBSCRIPTION" if live else "STRIPE_TEST_SUBSCRIPTION", "external_effects": 0}


def acknowledge_service(db, tenant_id, local_id, invoice_id, request, principal, *, live):
    binding, period, _, now = _exact_period(db, local_id, invoice_id, live, tenant_id=tenant_id, principal=principal)
    if request.paid_period_sha256 != period.evidence_sha256:
        raise HTTPException(409, "Paid service period digest differs")
    scope = binding["scope"]
    reference = artifact_digest(ACK, invoice_id, {"live": live})[:32]
    key = f"STRIPE-SERVICE-ACK-{local_id}-{reference}"
    value = {"scope": scope, "invoice_id": invoice_id, "subscription_id": local_id,
             "paid_period_sha256": period.evidence_sha256, "subscriber_id": binding["subscriber_id"],
             "tenant_id": binding["tenant_id"], "basis": "BUYER_SERVICE_ASSERTION" if live else "SYNTHETIC_SERVICE_ACK"}
    existing = _read_record(db, key, ACK, scope)
    if existing is not None:
        if any(existing.get(field) != expected for field, expected in value.items()):
            raise HTTPException(409, "Recorded service acknowledgment conflicts")
        return existing
    return _write_record(db, key, ACK, {**value, "acknowledged_at": now.isoformat()})


def recognize_service(db, local_id, invoice_id, request, *, live):
    binding, period, verified, now = _exact_period(db, local_id, invoice_id, live)
    scope = binding["scope"]
    reference = artifact_digest(ACK, invoice_id, {"live": live})[:32]
    ack = _read_record(db, f"STRIPE-SERVICE-ACK-{local_id}-{reference}", ACK, scope)
    if (ack is None or ack["sha256"] != request.acknowledgment_sha256
            or ack["paid_period_sha256"] != period.evidence_sha256
            or (ack["subscription_id"], ack["invoice_id"], ack["subscriber_id"], ack["tenant_id"])
            != (local_id, invoice_id, binding["subscriber_id"], binding["tenant_id"])):
        raise HTTPException(409, "Exact subscriber acknowledgment required")
    bank = invoice_bank_summary(db, invoice_id, scope, held=False, live=live, lock=True)
    if bank is None or bank["status"] != "RECONCILIATION_RECORDED":
        raise HTTPException(409, "Intact exact invoice bank settlement required")
    gross = verified["captured_minor"]
    if gross > bank["batch_liability_minor"]:
        raise HTTPException(409, "Service principal exceeds the original liability")
    began = datetime.fromtimestamp(period.period_start, timezone.utc).date()
    finished = (datetime.fromtimestamp(period.period_end, timezone.utc) - timedelta(seconds=1)).date()
    posting = max(finished, date.fromisoformat(bank["booked_on"]), datetime.fromisoformat(ack["acknowledged_at"]).date())
    if posting > now.date():
        raise HTTPException(409, "Future-dated service recognition not supported")
    key = f"STRIPE-SERVICE-REVENUE-{local_id}-{reference}"
    value = {"scope": scope, "invoice_id": invoice_id, "subscription_id": local_id,
             "paid_period_sha256": period.evidence_sha256, "acknowledgment_sha256": ack["sha256"],
             "batch_sha256": bank["sha256"], "posting_date": posting.isoformat(),
             "basis": "ACKNOWLEDGED_CAD_SERVICE" if live else "SYNTHETIC_SERVICE_RELEASE",
             "eligible_liability_minor": gross, "recognized_revenue_minor": gross if live else None,
             "available_cash_minor": None}
    prior = _read_record(db, key, RELEASE, scope)
    if prior is not None:
        entry = db.get(JournalEntry, prior["ledger_entry_id"]) if live else None
        if (any(prior.get(field) != expected for field, expected in value.items())
                or (live and (entry is None or entry.source != SOURCE or entry.source_ref != key))
                or (not live and prior["ledger_entry_id"] is not None)):
            raise HTTPException(409, "Recorded recognition conflicts with current evidence")
        return prior
    try:
        value["ledger_entry_id"] = _release_posting(
            db, key, scope, posting, bank, gross, served_from=began, served_until=finished,
        ) if live else None
        digest = artifact_digest(RELEASE, key, value)
        _event(db, event_id=key, legacy_instance_id=scope["legacy_instance_id"], event_type=RELEASE,
               message="Exact recurring service liability release", payload={"value": value, "sha256": digest})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent recurring release; replay the exact receipt") from None
    return {**value, "sha256": digest}
