"""Reconcile a single exact recurring invoice from the durable signed event journal."""
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import and_, exists, inspect, or_, select

from app.models.stripe_finance import StripeFinancialEvent
from app.models.stripe_recurring import StripePaidPeriod, StripeRecurringAttempt, StripeSaaSBinding
from app.services.stripe_finance import _event_receipt
from app.services.stripe_recurring import InvoiceProofIn, _now, _ready, apply_paid_invoice


def reconcile_due_invoice(db, client, *, live, now=None):
    _ready(db)
    if not inspect(db.connection()).has_table(StripeRecurringAttempt.__tablename__):
        raise HTTPException(503, "Recurring worker migration is unavailable")
    now = now or _now()
    snapshot = StripeFinancialEvent.snapshot
    candidate = db.scalar(select(StripeFinancialEvent).outerjoin(
        StripeRecurringAttempt, StripeRecurringAttempt.event_id == StripeFinancialEvent.event_id,
    ).where(
        StripeFinancialEvent.livemode == live,
        snapshot["kind"].as_string() == "invoice.paid",
        snapshot["local_subscription_id"].as_integer().is_not(None),
        ~exists(select(StripePaidPeriod.invoice_id).where(StripePaidPeriod.invoice_id == snapshot["object_id"].as_string())),
        or_(StripeRecurringAttempt.event_id.is_(None), and_(
            StripeRecurringAttempt.state == "retry_pending", StripeRecurringAttempt.retry_at <= now,
        )),
    ).order_by(StripeFinancialEvent.received_at, StripeFinancialEvent.event_id).limit(1)
        .with_for_update(of=StripeFinancialEvent, skip_locked=True))
    if candidate is None:
        return {"status": "idle"}
    event_id = candidate.event_id
    invoice_id = candidate.snapshot["object_id"]
    try:
        _event_receipt(candidate, True)
        local_id = candidate.snapshot["local_subscription_id"]
        binding = db.get(StripeSaaSBinding, local_id)
        if (binding is None or binding.livemode is not live
                or binding.binding_sha256 != candidate.snapshot["subscription_binding_sha256"]):
            raise HTTPException(409, "Signed invoice binding mismatch")
        result = apply_paid_invoice(db, local_id, InvoiceProofIn(event_id=event_id), live=live, client=client)
        attempt = db.get(StripeRecurringAttempt, event_id, with_for_update=True)
        if attempt:
            attempt.state = "reconciled"
            attempt.retry_at = None
            db.commit()
        return {"status": "recorded", "basis": result["basis"]}
    except HTTPException as error:
        db.rollback()
        # Re-lock the immutable signed event before writing failure state.
        db.get(StripeFinancialEvent, event_id, with_for_update=True)
        if db.get(StripePaidPeriod, invoice_id) is not None:
            return {"status": "already_recorded"}
        attempt = db.get(StripeRecurringAttempt, event_id, with_for_update=True)
        if attempt is None:
            attempt = StripeRecurringAttempt(event_id=event_id, attempts=0, state="retry_pending")
            db.add(attempt)
        attempt.attempts += 1
        retry = error.status_code in (429, 503) and attempt.attempts < 8
        attempt.state = "retry_pending" if retry else "review_required"
        attempt.retry_at = now + timedelta(seconds=min(3600, 30 * 2 ** (attempt.attempts - 1))) if retry else None
        db.commit()
        return {"status": attempt.state, "attempts": attempt.attempts}
