"""Independently verify exact CAD refunds and post their processor corrections."""
from datetime import datetime, timezone
from decimal import Decimal
import os

from fastapi import HTTPException
from pydantic import field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.accounting.models import Account, JournalEntry, JournalLine
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event
from app.services.specialist_triggers import outcome_scope_key
from app.services.stripe_bank_booking import _payout_failed, bank_batch_summary, require_open_period
from app.services.stripe_finance import (
    DISPUTE_EVENTS, _event_receipt, _provider_object, minor_amount, stripe_id, stripe_readback_client,
)
from app.services.stripe_fulfillment import _locked_order, _read_record
from app.services.stripe_orders import inspect_binding
from app.services.stripe_revenue_release import RELEASE, SOURCE as RELEASE_SOURCE

CORRECTION = "STRIPE_FULL_REFUND_PROCESSOR_CORRECTION"
PARTIAL = "STRIPE_PARTIAL_REFUND_PROCESSOR_CORRECTION"
SOURCE = "stripe_refund_processor_correction"


class RefundCorrectionIn(StrictModel):
    refund_id: str
    signed_event_id: str

    @field_validator("refund_id", "signed_event_id")
    @classmethod
    def native_id(cls, value, info):
        if not stripe_id(value, "re" if info.field_name == "refund_id" else "evt"):
            raise ValueError("Native Stripe refund and event identities required")
        return value


def refund_evidence(client, account_id, order, event, refund_id, now, prior_minor=0):
    if (event.get("kind"), event.get("payment_intent_id"), event.get("currency")) != (
        "charge.refunded", order["payment_intent_id"], "cad",
    ) or not stripe_id(event.get("charge_id"), "ch"):
        raise HTTPException(409, "An exact signed refund event is required")
    _provider_object(client, "/v1/account", account_id, "account")
    charge = _provider_object(client, f"/v1/charges/{event['charge_id']}", event["charge_id"], "charge")
    gross = order["amount_minor"]
    cumulative = event.get("amount_minor")
    current = charge.get("amount_refunded")
    if (charge.get("livemode") is not order["livemode"] or charge.get("payment_intent") != order["payment_intent_id"]
            or charge.get("currency") != "cad" or charge.get("captured") is not True
            or charge.get("amount_captured") != gross
            or charge.get("disputed") is not False or not minor_amount(current) or not minor_amount(cumulative)
            or not 0 <= prior_minor < cumulative <= current <= gross
            or charge.get("refunded") is not (current == gross)):
        raise HTTPException(409, "Signed cumulative refund does not reconcile with the independently read charge")
    refund = _provider_object(client, f"/v1/refunds/{refund_id}", refund_id, "refund")
    transaction_id = refund.get("balance_transaction")
    refunded = cumulative - prior_minor
    if (refund.get("charge") != charge["id"] or refund.get("payment_intent") != order["payment_intent_id"]
            or refund.get("status") != "succeeded" or refund.get("currency") != "cad"
            or not minor_amount(refund.get("amount")) or refund["amount"] != refunded
            or refund.get("failure_balance_transaction") or not stripe_id(transaction_id, "txn")):
        raise HTTPException(409, "Successful Stripe refund does not match the next exact cumulative movement")
    txn = _provider_object(client, f"/v1/balance_transactions/{transaction_id}", transaction_id, "balance_transaction")
    stamp = txn.get("available_on")
    if (txn.get("source") != refund_id or txn.get("currency") != "cad"
            or txn.get("type") not in {"refund", "payment_refund"} or txn.get("status") != "available"
            or any(type(txn.get(key)) is not int for key in ("amount", "net", "fee"))
            or (txn["amount"], txn["net"], txn["fee"]) != (-refunded, -refunded, 0)
            or type(stamp) is not int or not 0 < stamp <= int(now.timestamp())):
        raise HTTPException(409, "Refund clearing movement is pending or has unmatched adjustments")
    return {"refund_id": refund_id, "refund_balance_id": transaction_id, "charge_id": charge["id"],
            "refund_minor": refunded, "processor_posted_on": datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()}


def _post_correction(db, scope, key, posted, gross, bank, prior_release, *, fee=0, source=SOURCE):
    if (os.getenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED") != "1"
            or os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(503, "Processor refund accounting is not authorized for this scope")
    require_open_period(db, posted)
    clearing = db.scalar(select(Account).filter_by(code=os.getenv("VALHALLA_STRIPE_BOOK_CLEARING"),
                                                    type="asset", active=True, currency="CAD"))
    code = "VALHALLA_STRIPE_BOOK_REFUND_CONTRA_INCOME" if prior_release else "VALHALLA_STRIPE_BOOK_OBLIGATIONS"
    debit = db.scalar(select(Account).filter_by(code=os.getenv(code), active=True, currency="CAD",
                                                 type="income" if prior_release else "liability"))
    if clearing is None or debit is None:
        raise HTTPException(503, "Approved processor correction accounts are required")
    if prior_release is None:
        original = db.get(JournalEntry, bank["ledger_entry_id"])
        original_tag = artifact_digest("stripe_booking_scope", original.source_ref, scope)
        original_liability = db.scalars(select(JournalLine).filter_by(
            entry_id=original.id, account_id=debit.id, tag=original_tag,
        )).all()
        if (len(original_liability) != 1 or original_liability[0].debit != 0
                or original_liability[0].credit != Decimal(bank["batch_liability_minor"]) / 100):
            raise HTTPException(409, "Refund liability account differs from the original bank booking")
    if db.scalar(select(JournalEntry.id).filter_by(source=source, source_ref=key).limit(1)) is not None:
        raise HTTPException(409, "Refund correction exists without an exact evidence receipt")
    entry = JournalEntry(entry_date=posted, memo="Stripe correction in processor clearing", source=source, source_ref=key)
    db.add(entry)
    db.flush()
    amount = Decimal(gross) / 100
    tag = artifact_digest("stripe_refund_scope", key, scope)
    db.add_all([
        JournalLine(entry_id=entry.id, account_id=debit.id, debit=amount, credit=0, tag=tag),
        JournalLine(entry_id=entry.id, account_id=clearing.id, debit=0, credit=amount + Decimal(fee) / 100, tag=tag),
    ])
    if fee:
        expense = db.scalar(select(Account).filter_by(code=os.getenv("VALHALLA_STRIPE_BOOK_FEES"),
                                                       type="expense", active=True, currency="CAD"))
        if expense is None:
            raise HTTPException(503, "Approved processor fee expense account is required")
        db.add(JournalLine(entry_id=entry.id, account_id=expense.id, debit=Decimal(fee) / 100, credit=0, tag=tag))
    return entry.id


def record_refund_correction(db, order_id, request, *, client, account_id, live):
    order, binding = _locked_order(db, order_id, live)
    scope = binding["scope"]
    event = db.get(StripeFinancialEvent, request.signed_event_id)
    if event is None or event.livemode is not live or account_id != binding["stripe_account_id"]:
        raise HTTPException(409, "Matching signed refund and processor account are required")
    _event_receipt(event, True)
    projection = inspect_binding(db, order_id, live=live)
    bank = bank_batch_summary(db, order_id, projection, live=live)
    if bank is None or _payout_failed(db, bank["payout_id"], live):
        raise HTTPException(409, "A booked original batch without a separate payout failure is required")
    capture = db.scalar(select(StripeBalanceEvidence).filter_by(
        livemode=live, payment_intent_id=order.payment_intent_id,
    ))
    if capture is None or capture.evidence.get("charge_id") != event.snapshot.get("charge_id"):
        raise HTTPException(409, "Refund charge differs from the originally reconciled capture")
    release_key = f"STRIPE-DELIVERY-REVENUE-{order_id}"
    release = _read_record(db, release_key, RELEASE, scope)
    return _record_matched_refund(
        db, request, client, account_id, binding, event, bank, release_key, release,
        target=str(order_id), identity={"order_id": str(order_id)}, live=live,
    )


def _record_matched_refund(db, request, client, account_id, binding, event, bank, release_key, release, *,
                           target, identity, live):
    scope = binding["scope"]
    dispute = db.scalar(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == live,
        StripeFinancialEvent.snapshot["kind"].as_string().in_(DISPUTE_EVENTS),
        StripeFinancialEvent.snapshot["charge_id"].as_string() == event.snapshot["charge_id"],
    ).limit(1))
    if dispute is not None:
        _event_receipt(dispute, True)
        raise HTTPException(409, "A separate signed dispute requires professional correction review")
    prefix = f"STRIPE-PARTIAL-REFUND-{target}-"
    full_key = f"STRIPE-FULL-REFUND-{target}"
    full = _read_record(db, full_key, CORRECTION, scope)
    keys = db.scalars(select(LegacyOrchestrationEvent.event_id).where(
        LegacyOrchestrationEvent.event_id.startswith(prefix, autoescape=True),
    )).all()
    partials = sorted((_read_record(db, key, PARTIAL, scope) for key in keys),
                      key=lambda item: item["cumulative_refund_minor"])
    committed = 0
    for receipt in partials:
        committed += receipt["refund_minor"]
        if any(receipt.get(field) != value for field, value in identity.items()) or receipt["cumulative_refund_minor"] != committed:
            raise HTTPException(409, "Refund correction history is contradictory")
    key = prefix + artifact_digest("stripe_refund_identity", request.refund_id, {"live": live})[:32]
    prior = _read_record(db, key, PARTIAL, scope)
    if full is not None and full["refund_id"] == request.refund_id:
        key, prior = full_key, full
    kind = CORRECTION if key == full_key else PARTIAL
    if prior is not None:
        if (any(prior.get(field) != value for field, value in identity.items())
                or prior["signed_refund_sha256"] != event.snapshot_sha256 or prior["bank_batch_sha256"] != bank["sha256"]):
            raise HTTPException(409, "Refund evidence differs from the recorded correction")
        preceding = prior.get("cumulative_refund_minor", prior["refund_minor"]) - prior["refund_minor"]
        current = refund_evidence(client, account_id, binding, event.snapshot, request.refund_id,
                                  datetime.now(timezone.utc), prior_minor=preceding)
        if any(prior.get(field) != detail for field, detail in current.items()):
            raise HTTPException(409, "Refund correction differs from fresh processor evidence")
        posting = db.get(JournalEntry, prior["ledger_entry_id"]) if live else None
        if (live and (posting is None or posting.source != SOURCE or posting.source_ref != key)) or (
            not live and prior["ledger_entry_id"] is not None
        ):
            raise HTTPException(409, "Refund accounting entry is contradictory")
        return prior
    if full is not None:
        raise HTTPException(409, "This order already has a full refund correction")
    match = refund_evidence(client, account_id, binding, event.snapshot, request.refund_id,
                            datetime.now(timezone.utc), prior_minor=committed)
    if match["refund_minor"] == binding["amount_minor"]:
        key, kind = full_key, CORRECTION
    if live and release is not None:
        entry = db.get(JournalEntry, release["ledger_entry_id"])
        if (entry is None or entry.source != RELEASE_SOURCE or entry.source_ref != release_key
                or release["recognized_revenue_minor"] != binding["amount_minor"]):
            raise HTTPException(409, "Prior delivery income posting is unavailable or contradictory")
    value = {"scope": scope, **identity, "bank_batch_sha256": bank["sha256"],
             "signed_refund_sha256": event.snapshot_sha256, **match,
             "basis": "STRIPE_CAD_PROCESSOR_CORRECTION" if live else "SYNTHETIC_REFUND_CORRECTION",
             "corrects_delivery_income": release is not None, "bank_debit_confirmed": False,
             "available_cash_minor": None, "cash_hold_released": False}
    if kind == PARTIAL:
        value["cumulative_refund_minor"] = committed + match["refund_minor"]
    try:
        posted_on = max(bank["booked_on"], match["processor_posted_on"])
        if release is not None:
            posted_on = max(posted_on, release["posting_date"])
        value["ledger_entry_id"] = (_post_correction(db, scope, key, datetime.fromisoformat(posted_on).date(),
                                                    match["refund_minor"], bank, release) if live else None)
        digest = artifact_digest(kind, key, value)
        unique = "STRIPE-REFUND-TX-" + artifact_digest("stripe_refund_balance", match["refund_balance_id"],
                                                     {"live": live})[:40]
        _event(db, event_id=unique, legacy_instance_id=scope["legacy_instance_id"], event_type=kind,
               message="Refund transaction consumed", payload={**identity, "sha256": digest})
        _event(db, event_id=key, legacy_instance_id=scope["legacy_instance_id"], event_type=kind,
               message="Exact independently verified Stripe refund correction", payload={"value": value, "sha256": digest})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Refund transaction already consumed; replay the exact correction") from None
    return {**value, "sha256": digest}


def configured_refund_correction(db, order_id, request, *, live):
    with stripe_readback_client(live=live) as (client, account_id):
        return record_refund_correction(db, order_id, request, client=client, account_id=account_id, live=live)


def configured_subscription_refund(db, local_id, invoice_id, request, *, live):
    from app.models.stripe_recurring import StripePaidPeriod
    from app.services.stripe_bank_booking import invoice_bank_summary
    from app.services.stripe_recurring import _binding, _period_value
    from app.services.stripe_subscription_delivery import ACK, RELEASE as SERVICE_RELEASE

    if not stripe_id(invoice_id, "in"):
        raise HTTPException(422, "Native Stripe invoice identity required")
    with stripe_readback_client(live=live) as (client, account_id):
        row, binding, _ = _binding(db, local_id, live, lock=True)
        period = db.get(StripePaidPeriod, invoice_id)
        event = db.get(StripeFinancialEvent, request.signed_event_id)
        if (period is None or period.binding_id != local_id or account_id != binding["stripe_account_id"]
                or event is None or event.livemode is not live):
            raise HTTPException(409, "Exact subscription, paid period and signed refund are required")
        paid = _period_value(row, period)
        _event_receipt(event, True)
        if paid["charge_id"] != event.snapshot.get("charge_id"):
            raise HTTPException(409, "Refund charge differs from the settled invoice capture")
        scope = binding["scope"]
        bank = invoice_bank_summary(db, invoice_id, scope, held=False, live=live, lock=True)
        if bank is None or bank["status"] != "RECONCILIATION_RECORDED":
            raise HTTPException(409, "Original invoice bank settlement without a payout correction is required")
        reference = artifact_digest(ACK, invoice_id, {"live": live})[:32]
        release_key = f"STRIPE-SERVICE-REVENUE-{local_id}-{reference}"
        release = _read_record(db, release_key, SERVICE_RELEASE, scope)
        if release is not None and (release["paid_period_sha256"] != period.evidence_sha256
                                    or release["batch_sha256"] != bank["sha256"]):
            raise HTTPException(409, "Prior service recognition did not match this invoice settlement")
        financial = {"scope": scope, "amount_minor": paid["captured_minor"],
                     "payment_intent_id": paid["payment_intent_id"], "livemode": live}
        identity = {"subscription_id": local_id, "invoice_id": invoice_id, "paid_period_sha256": period.evidence_sha256}
        return _record_matched_refund(
            db, request, client, account_id, financial, event, bank, release_key, release,
            target=f"SERVICE-{local_id}-{reference}", identity=identity, live=live,
        )
