"""Release one exact paid delivery obligation after accounting settlement."""
from datetime import date
from decimal import Decimal
import os

from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.accounting.models import Account, JournalEntry, JournalLine, Period
from app.loki.evidence import artifact_digest
from app.schemas.market_intelligence import StrictModel
from app.services.stripe_bank_booking import bank_batch_summary, require_open_period
from app.services.stripe_fulfillment import ACCEPTANCE, GRANT, OFFERED, REVOKED, _locked_order, _read_record
from app.services.stripe_orders import inspect_binding
from app.services.specialist_triggers import outcome_scope_key
from app.services.prime_business_execution import _emergency_stop_active, _event

RELEASE = "STRIPE_DELIVERY_LIABILITY_RELEASED"
SOURCE = "stripe_delivery_liability_release"


class DeliveryReleaseIn(StrictModel):
    acknowledgment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _release_posting(db, key, scope, posted_on, bank, gross, *, served_from=None, served_until=None):
    if (os.getenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED") != "1"
            or os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(503, "Revenue posting is not authorized for this scope")
    if _emergency_stop_active(db):
        raise HTTPException(409, "Emergency stop holds new revenue postings")
    require_open_period(db, posted_on)
    liability = db.scalar(select(Account).filter_by(code=os.getenv("VALHALLA_STRIPE_BOOK_OBLIGATIONS"),
                                                    type="liability", active=True, currency="CAD"))
    income = db.scalar(select(Account).filter_by(code=os.getenv("VALHALLA_STRIPE_BOOK_DELIVERY_INCOME"),
                                                  type="income", active=True, currency="CAD"))
    if served_from is not None:
        window = db.scalar(select(Period).where(Period.start_date <= posted_on, Period.end_date >= posted_on))
        if not window.start_date <= served_from <= served_until <= window.end_date:
            raise HTTPException(409, "Cross-period service needs a separately approved accrual and posting schedule")
    original = db.get(JournalEntry, bank["ledger_entry_id"])
    if liability is None or income is None or original is None:
        raise HTTPException(503, "Approved income, liability and bank journal accounts are required")
    liability_tag = artifact_digest("stripe_booking_scope", original.source_ref, scope)
    amounts = db.scalars(select(JournalLine).filter_by(entry_id=original.id, account_id=liability.id,
                                                       tag=liability_tag)).all()
    amount = Decimal(gross) / 100
    if len(amounts) != 1 or amounts[0].debit != 0 or amounts[0].credit != Decimal(bank["batch_liability_minor"]) / 100:
        raise HTTPException(409, "Open liability differs from the matched bank booking")
    if db.scalar(select(JournalEntry.id).filter_by(source=SOURCE, source_ref=key).limit(1)) is not None:
        raise HTTPException(409, "Accounting release exists without an exact delivery receipt")
    entry = JournalEntry(entry_date=posted_on, memo="Recognize acknowledged paid product delivery",
                         source=SOURCE, source_ref=key)
    db.add(entry)
    db.flush()
    db.add_all([
        JournalLine(entry_id=entry.id, account_id=liability.id, debit=amount, credit=0, tag=liability_tag),
        JournalLine(entry_id=entry.id, account_id=income.id, debit=0, credit=amount, tag=liability_tag),
    ])
    return entry.id


def recognize_delivery(db, order_id, request, *, live):
    _, binding = _locked_order(db, order_id, live)
    scope = binding["scope"]
    grant = _read_record(db, f"STRIPE-DELIVERY-{order_id}", GRANT, scope)
    ack = _read_record(db, f"STRIPE-DELIVERY-ACK-{order_id}", ACCEPTANCE, scope)
    if (grant is None or ack is None or ack["sha256"] != request.acknowledgment_sha256
            or ack["grant_sha256"] != grant["sha256"] or ack.get("buyer_acknowledged") is not True
            or ack.get("order_id") != str(order_id) or ack.get("tenant_id") != grant["tenant_id"]
            or ack.get("subscriber_id") != grant["subscriber_id"]
            or not ack.get("acknowledged_on")
            or _read_record(db, f"STRIPE-DELIVERY-REVOKE-{order_id}", REVOKED, scope)):
        raise HTTPException(409, "Exact intact buyer acknowledgment and delivery grant are required")
    if live:
        offer = _read_record(db, f"STRIPE-DELIVERY-OFFER-{order_id}", OFFERED, scope)
        if offer is None or offer["grant_sha256"] != grant["sha256"] or ack["basis"] != "PAID_ONE_TIME_PRODUCT":
            raise HTTPException(409, "Exact live delivery offer evidence is required")
    projection = inspect_binding(db, order_id, live=live)
    bank = bank_batch_summary(db, order_id, projection, live=live)
    if bank is None or bank["status"] != "RECONCILIATION_RECORDED":
        raise HTTPException(409, "Reconciled bank batch without correction hold is required")
    if grant["order_sha256"] != projection["order"]["sha256"]:
        raise HTTPException(409, "Delivery grant does not match the settled order")
    gross = projection["processor_evidence"]["gross_minor"]
    posted_on = max(date.fromisoformat(bank["booked_on"]), date.fromisoformat(ack["acknowledged_on"]))
    key = f"STRIPE-DELIVERY-REVENUE-{order_id}"
    value = {"scope": scope, "order_id": str(order_id), "acknowledgment_sha256": ack["sha256"],
             "batch_sha256": bank["sha256"], "posting_date": posted_on.isoformat(),
             "basis": "ACKNOWLEDGED_CAD_DELIVERY" if live else "SYNTHETIC_LIABILITY_RELEASE_PREVIEW",
             "eligible_liability_minor": gross, "recognized_revenue_minor": gross if live else None,
             "available_cash_minor": None}
    prior = _read_record(db, key, RELEASE, scope)
    if prior is not None:
        original = {k: v for k, v in prior.items() if k not in {"sha256", "ledger_entry_id"}}
        posting_id = prior["ledger_entry_id"]
        entry = db.get(JournalEntry, posting_id) if live and type(posting_id) is int else None
        if original != value or (live and (entry is None or entry.source != SOURCE or entry.source_ref != key)) or (
            not live and posting_id is not None
        ):
            raise HTTPException(409, "Delivery release differs from recorded evidence")
        return prior
    try:
        posting = _release_posting(db, key, scope, posted_on, bank, gross) if live else None
        value["ledger_entry_id"] = posting
        digest = artifact_digest(RELEASE, key, value)
        _event(db, event_id=key, legacy_instance_id=scope["legacy_instance_id"], event_type=RELEASE,
               message="Exact paid delivery liability release", payload={"value": value, "sha256": digest})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent accounting release; replay the exact receipt") from None
    return {**value, "sha256": digest}


def delivery_evidence_summary(db, order_id, projection, bank, *, live):
    scope = projection["order"]["scope"]
    grant = _read_record(db, f"STRIPE-DELIVERY-{order_id}", GRANT, scope)
    if grant is None:
        return None
    basis = "PAID_ONE_TIME_PRODUCT" if live else "SYNTHETIC_DELIVERY_REHEARSAL"
    if grant["order_sha256"] != projection["order"]["sha256"] or grant["basis"] != basis:
        raise HTTPException(409, "Delivery grant evidence does not match this order")
    revoked = _read_record(db, f"STRIPE-DELIVERY-REVOKE-{order_id}", REVOKED, scope)
    if (revoked is not None or projection["status"] == "REFUND_REVIEW_REQUIRED"
            or (bank and bank["status"] == "CORRECTION_REVIEW_REQUIRED")):
        return {"basis": basis, "status": "DELIVERY_REVIEW_REQUIRED",
                "recognized_revenue_minor": None, "available_cash_minor": None}
    ack = _read_record(db, f"STRIPE-DELIVERY-ACK-{order_id}", ACCEPTANCE, scope)
    if ack is not None and ack.get("grant_sha256") != grant["sha256"]:
        raise HTTPException(409, "Buyer acknowledgment differs from the delivery grant")
    receipt_key = f"STRIPE-DELIVERY-REVENUE-{order_id}"
    release = _read_record(db, receipt_key, RELEASE, scope)
    status = "BUYER_ACKNOWLEDGED" if ack else "DELIVERY_AUTHORIZED"
    if release is not None:
        if (ack is None or bank is None or release["acknowledgment_sha256"] != ack["sha256"]
                or release["batch_sha256"] != bank["sha256"]):
            raise HTTPException(409, "Delivery release differs from current settlement evidence")
        if live:
            ledger_id = release["ledger_entry_id"]
            ledger = db.get(JournalEntry, ledger_id) if type(ledger_id) is int else None
            if ledger is None or ledger.source != SOURCE or ledger.source_ref != receipt_key:
                raise HTTPException(409, "Delivery release posting is unavailable")
        elif release["ledger_entry_id"] is not None or release["recognized_revenue_minor"] is not None:
            raise HTTPException(409, "Synthetic delivery cannot recognize revenue")
        status = "LIABILITY_RELEASE_RECORDED" if live else "LIABILITY_RELEASE_REHEARSED"
    return {"basis": basis, "status": status,
            "recognized_revenue_minor": release["recognized_revenue_minor"] if release else None,
            "available_cash_minor": None}


def scoped_delivery_outcomes(db, scope, *, live):
    """Read current release outcomes for specialist evidence, without issuing cash authority."""
    from uuid import UUID

    from sqlalchemy import inspect
    from app.models.completion_registry import LegacyOrchestrationEvent
    from app.services.prime_business_execution import _json

    journal = LegacyOrchestrationEvent
    if not inspect(db.connection()).has_table(journal.__tablename__):
        return []
    basis = "ACKNOWLEDGED_CAD_DELIVERY" if live else "SYNTHETIC_LIABILITY_RELEASE_PREVIEW"
    rows = db.scalars(select(journal).where(
        journal.event_type == RELEASE, journal.legacy_instance_id == scope["legacy_instance_id"],
    ).order_by(journal.id.desc()).execution_options(yield_per=20))
    result = []
    for row in rows:
        receipt = _json(row.payload_json, {})
        data = receipt.get("value") if isinstance(receipt, dict) else None
        if not isinstance(data, dict) or data.get("scope") != scope or data.get("basis") != basis:
            continue
        try:
            order_id = UUID(data["order_id"])
            if row.event_id != f"STRIPE-DELIVERY-REVENUE-{order_id}":
                raise ValueError
            projection = inspect_binding(db, order_id, live=live)
            bank = bank_batch_summary(db, order_id, projection, live=live)
            summary = delivery_evidence_summary(db, order_id, projection, bank, live=live)
            if summary is None:
                raise ValueError
        except (HTTPException, ValueError, KeyError, TypeError):
            summary = {"status": "DELIVERY_EVIDENCE_CONFLICT", "recognized_revenue_minor": None,
                       "available_cash_minor": None}
        result.append({**summary, "receipt_id": row.event_id, "basis": basis, "external_authority": False})
        if len(result) == 10:
            break
    return result
