"""Book bounded, independently verified terminal CAD chargebacks."""
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.accounting.models import JournalEntry
from app.loki.evidence import artifact_digest
from app.models.stripe_finance import StripeFinancialEvent
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event
from app.services.stripe_bank_booking import _payout_failed, bank_batch_summary
from app.services.stripe_finance import (
    ACTIVE_DISPUTE_STATUSES, _event_receipt, _provider_object, minor_amount, stripe_id, stripe_readback_client,
)
from app.services.stripe_fulfillment import _locked_order, _read_record
from app.services.stripe_orders import inspect_binding
from app.services.stripe_refund_correction import _post_correction
from app.services.stripe_revenue_release import RELEASE, SOURCE as RELEASE_SOURCE

KIND = "STRIPE_FINAL_CHARGEBACK_PROCESSOR_CORRECTION"
SOURCE = "stripe_dispute_processor_correction"


class ChargebackIn(StrictModel):
    signed_event_id: str


def _debit(client, snapshot, order, charge_id, now):
    gross, dispute_id = order["amount_minor"], snapshot["object_id"]
    disputed = snapshot.get("amount_minor")
    expected = (charge_id, order["payment_intent_id"], "cad")
    if (not minor_amount(disputed) or not 0 < disputed <= gross
            or (snapshot.get("charge_id"), snapshot.get("payment_intent_id"), snapshot.get("currency")) != expected
            or snapshot.get("native_status") != "lost"
            or snapshot.get("kind") != "charge.dispute.closed" or not stripe_id(dispute_id, "du")):
        raise HTTPException(409, "An exact signed lost dispute within the captured amount is required")
    _provider_object(client, "/v1/account", order["stripe_account_id"], "account")
    charge = _provider_object(client, f"/v1/charges/{charge_id}", charge_id, "charge")
    if (charge.get("livemode") is not order["livemode"] or charge.get("disputed") is not True
            or charge.get("amount_refunded") != 0 or charge.get("payment_intent") != order["payment_intent_id"]
            or charge.get("currency") != "cad" or charge.get("amount_captured") != gross):
        raise HTTPException(409, "Charge is inconsistent, partially refunded or outside the exact dispute")
    dispute = _provider_object(client, f"/v1/disputes/{dispute_id}", dispute_id, "dispute")
    members = dispute.get("balance_transactions")
    if (dispute.get("livemode") is not order["livemode"] or dispute.get("status") != "lost"
            or not minor_amount(dispute.get("amount"))
            or (dispute.get("charge"), dispute.get("payment_intent"), dispute.get("currency"),
                dispute.get("amount")) != (*expected, disputed)
            or not isinstance(members, list) or len(members) != 1 or not isinstance(members[0], dict)
            or not stripe_id(members[0].get("id"), "txn")):
        raise HTTPException(409, "Only one exact terminal dispute debit is supported")
    txn = members[0]["id"]
    remote = _provider_object(client, f"/v1/balance_transactions/{txn}", txn, "balance_transaction")
    fee, posted = remote.get("fee"), remote.get("available_on")
    if (remote.get("source") not in {dispute_id, charge_id} or remote.get("currency") != "cad"
            or remote.get("type") != "adjustment" or remote.get("reporting_category") != "dispute"
            or remote.get("status") != "available"
            or type(remote.get("amount")) is not int or remote["amount"] != -disputed
            or not minor_amount(fee) or type(remote.get("net")) is not int or remote["net"] != -disputed - fee
            or type(posted) is not int or not 0 < posted <= int(now.timestamp())):
        raise HTTPException(409, "Processor dispute debit or fee did not reconcile")
    return {"dispute_id": dispute_id, "processor_balance_id": txn, "debit_minor": disputed, "fee_minor": fee,
            "processor_posted_on": datetime.fromtimestamp(posted, timezone.utc).date().isoformat()}


def configured_chargeback(db, order_id, request, *, live):
    with stripe_readback_client(live=live) as (client, account):
        _, binding = _locked_order(db, order_id, live)
        if not stripe_id(request.signed_event_id, "evt"):
            raise HTTPException(422, "Native Stripe event identity required")
        event = db.get(StripeFinancialEvent, request.signed_event_id)
        if account != binding["stripe_account_id"] or event is None or event.livemode is not live:
            raise HTTPException(409, "Scoped Stripe dispute evidence is unavailable")
        _event_receipt(event, True)
        projection = inspect_binding(db, order_id, live=live, include_held_evidence=True)
        bank = bank_batch_summary(db, order_id, projection, live=live)
        if bank is None or _payout_failed(db, bank["payout_id"], live) or projection["processor_evidence"] is None:
            raise HTTPException(409, "Original batch and capture evidence are required")
        scope = binding["scope"]
        charge_id = projection["processor_evidence"]["charge_id"]
        _deny_prior_refund(db, charge_id, live)
        _deny_superseded_loss(db, event)
        effect = _debit(client, event.snapshot, binding, charge_id, datetime.now(timezone.utc))
        key = f"STRIPE-CHARGEBACK-{order_id}"
        release_key = f"STRIPE-DELIVERY-REVENUE-{order_id}"
        release = _read_record(db, release_key, RELEASE, scope)
        value = {"scope": scope, "order_id": str(order_id), "bank_batch_sha256": bank["sha256"],
                 "signed_dispute_sha256": event.snapshot_sha256, **effect,
                 "corrects_delivery_income": release is not None, "bank_debit_confirmed": False,
                 "available_cash_minor": None, "basis": "STRIPE_CAD_CHARGEBACK" if live else "SYNTHETIC_CHARGEBACK"}
        return _record_chargeback(
            db, key, value, bank, release_key, release, captured_minor=binding["amount_minor"], live=live,
        )


def _deny_superseded_loss(db, event):
    snapshot = StripeFinancialEvent.snapshot
    candidates = db.scalars(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == event.livemode,
        snapshot["object_id"].as_string() == event.snapshot["object_id"],
        snapshot["kind"].as_string().in_((
            "charge.dispute.closed", "charge.dispute.updated", "charge.dispute.funds_reinstated",
        )),
        StripeFinancialEvent.event_id != event.event_id,
    )).all()
    lost_at = event.snapshot.get("provider_created_at")
    for candidate in candidates:
        _event_receipt(candidate, True)
        evidence = candidate.snapshot
        if (evidence["kind"] == "charge.dispute.funds_reinstated"
                or evidence.get("native_status") in ACTIVE_DISPUTE_STATUSES | {"won", "warning_closed", "prevented"}):
            observed_at = evidence.get("provider_created_at")
            if lost_at is None or observed_at is None or observed_at >= lost_at:
                raise HTTPException(409, "A reopened or reinstated dispute requires independent correction review")


def _deny_prior_refund(db, charge_id, live):
    refund = db.scalar(select(StripeFinancialEvent.event_id).where(
        StripeFinancialEvent.livemode == live,
        StripeFinancialEvent.snapshot["kind"].as_string() == "charge.refunded",
        StripeFinancialEvent.snapshot["charge_id"].as_string() == charge_id,
    ).limit(1))
    if refund is not None:
        raise HTTPException(409, "A prior refund requires separate adjustment review")


def _record_chargeback(db, key, value, bank, release_key, release, *, captured_minor, live):
    scope = value["scope"]
    if live and release is not None:
        posting = db.get(JournalEntry, release["ledger_entry_id"])
        if (posting is None or posting.source != RELEASE_SOURCE or posting.source_ref != release_key
                or release["recognized_revenue_minor"] != captured_minor):
            raise HTTPException(409, "Prior recognition is contradictory")
    previous = _read_record(db, key, KIND, scope)
    if previous is not None:
        if any(previous.get(k) != field for k, field in value.items()):
            raise HTTPException(409, "Chargeback evidence changed after accounting")
        entry = db.get(JournalEntry, previous["ledger_entry_id"]) if live else None
        if (live and (entry is None or entry.source != SOURCE or entry.source_ref != key)
                or not live and previous["ledger_entry_id"] is not None):
            raise HTTPException(409, "Chargeback entry failed integrity")
        return previous
    posted = max(bank["booked_on"], value["processor_posted_on"], release["posting_date"] if release else "")
    try:
        value["ledger_entry_id"] = _post_correction(
            db, scope, key, date.fromisoformat(posted), value["debit_minor"], bank, release,
            fee=value["fee_minor"], source=SOURCE,
        ) if live else None
        digest = artifact_digest(KIND, key, value)
        unique = "STRIPE-DISPUTE-TX-" + artifact_digest(KIND, value["processor_balance_id"], {"live": live})[:40]
        for reference, payload in ((unique, {"sha256": digest}), (key, {"value": value, "sha256": digest})):
            _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=KIND,
                   message="Independently matched Stripe chargeback", payload=payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Chargeback debit already consumed") from None
    return {**value, "sha256": digest}


def configured_subscription_chargeback(db, local_id, invoice_id, request, *, live):
    from app.models.stripe_recurring import StripePaidPeriod
    from app.services.stripe_bank_booking import invoice_bank_summary
    from app.services.stripe_recurring import _binding, _period_value
    from app.services.stripe_subscription_delivery import ACK, RELEASE as SERVICE_RELEASE

    if not stripe_id(invoice_id, "in") or not stripe_id(request.signed_event_id, "evt"):
        raise HTTPException(422, "Native Stripe invoice and event identities required")
    with stripe_readback_client(live=live) as (client, account):
        row, binding, _ = _binding(db, local_id, live, lock=True)
        period = db.get(StripePaidPeriod, invoice_id)
        event = db.get(StripeFinancialEvent, request.signed_event_id)
        if (period is None or period.binding_id != local_id or account != binding["stripe_account_id"]
                or event is None or event.livemode is not live):
            raise HTTPException(409, "Exact subscription, paid period and signed dispute are required")
        paid = _period_value(row, period)
        _event_receipt(event, True)
        scope = binding["scope"]
        bank = invoice_bank_summary(db, invoice_id, scope, held=False, live=live, lock=True)
        if bank is None or bank["status"] != "RECONCILIATION_RECORDED":
            raise HTTPException(409, "Original invoice bank settlement without a payout correction is required")
        financial = {"amount_minor": paid["captured_minor"], "payment_intent_id": paid["payment_intent_id"],
                     "stripe_account_id": account, "livemode": live}
        _deny_prior_refund(db, paid["charge_id"], live)
        _deny_superseded_loss(db, event)
        effect = _debit(client, event.snapshot, financial, paid["charge_id"], datetime.now(timezone.utc))
        reference = artifact_digest(ACK, invoice_id, {"live": live})[:32]
        release_key = f"STRIPE-SERVICE-REVENUE-{local_id}-{reference}"
        release = _read_record(db, release_key, SERVICE_RELEASE, scope)
        if release is not None and (release["paid_period_sha256"] != period.evidence_sha256
                                    or release["batch_sha256"] != bank["sha256"]):
            raise HTTPException(409, "Prior service recognition did not match this invoice settlement")
        key = f"STRIPE-SERVICE-CHARGEBACK-{local_id}-{reference}"
        value = {"scope": scope, "subscription_id": local_id, "invoice_id": invoice_id,
                 "paid_period_sha256": period.evidence_sha256, "bank_batch_sha256": bank["sha256"],
                 "signed_dispute_sha256": event.snapshot_sha256, **effect,
                 "corrects_delivery_income": release is not None, "bank_debit_confirmed": False,
                 "available_cash_minor": None, "basis": "STRIPE_CAD_CHARGEBACK" if live else "SYNTHETIC_CHARGEBACK"}
        return _record_chargeback(
            db, key, value, bank, release_key, release, captured_minor=paid["captured_minor"], live=live,
        )
