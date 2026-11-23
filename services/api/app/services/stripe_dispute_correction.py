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
from app.services.stripe_finance import _event_receipt, _provider_object, minor_amount, stripe_id, stripe_readback_client
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
    expected = (charge_id, order["payment_intent_id"], "cad", gross)
    if ((snapshot.get("charge_id"), snapshot.get("payment_intent_id"), snapshot.get("currency"),
         snapshot.get("amount_minor")) != expected or snapshot.get("native_status") != "lost"
            or snapshot.get("kind") != "charge.dispute.closed" or not stripe_id(dispute_id, "du")):
        raise HTTPException(409, "An exact signed full lost dispute is required")
    _provider_object(client, "/v1/account", order["stripe_account_id"], "account")
    charge = _provider_object(client, f"/v1/charges/{charge_id}", charge_id, "charge")
    if (charge.get("livemode") is not order["livemode"] or charge.get("disputed") is not True
            or charge.get("amount_refunded") != 0 or charge.get("payment_intent") != order["payment_intent_id"]
            or charge.get("currency") != "cad" or charge.get("amount_captured") != gross):
        raise HTTPException(409, "Charge is inconsistent, partially refunded or outside the exact dispute")
    dispute = _provider_object(client, f"/v1/disputes/{dispute_id}", dispute_id, "dispute")
    members = dispute.get("balance_transactions")
    if (dispute.get("livemode") is not order["livemode"] or dispute.get("status") != "lost"
            or (dispute.get("charge"), dispute.get("payment_intent"), dispute.get("currency"),
                dispute.get("amount")) != expected
            or not isinstance(members, list) or len(members) != 1 or not isinstance(members[0], dict)
            or not stripe_id(members[0].get("id"), "txn")):
        raise HTTPException(409, "Only one exact terminal dispute debit is supported")
    txn = members[0]["id"]
    remote = _provider_object(client, f"/v1/balance_transactions/{txn}", txn, "balance_transaction")
    fee, posted = remote.get("fee"), remote.get("available_on")
    if (remote.get("source") not in {dispute_id, charge_id} or remote.get("currency") != "cad"
            or remote.get("type") != "adjustment" or remote.get("reporting_category") != "dispute"
            or remote.get("status") != "available" or remote.get("amount") != -gross
            or not minor_amount(fee) or type(remote.get("net")) is not int or remote["net"] != -gross - fee
            or type(posted) is not int or not 0 < posted <= int(now.timestamp())):
        raise HTTPException(409, "Processor dispute debit or fee did not reconcile")
    return {"dispute_id": dispute_id, "processor_balance_id": txn, "debit_minor": gross, "fee_minor": fee,
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
        refund = db.scalar(select(StripeFinancialEvent.event_id).where(
            StripeFinancialEvent.livemode == live,
            StripeFinancialEvent.snapshot["kind"].as_string() == "charge.refunded",
            StripeFinancialEvent.snapshot["charge_id"].as_string() == charge_id,
        ).limit(1))
        if refund is not None:
            raise HTTPException(409, "A prior refund requires separate adjustment review")
        effect = _debit(client, event.snapshot, binding, charge_id, datetime.now(timezone.utc))
        key = f"STRIPE-CHARGEBACK-{order_id}"
        release_key = f"STRIPE-DELIVERY-REVENUE-{order_id}"
        release = _read_record(db, release_key, RELEASE, scope)
        if live and release is not None:
            posting = db.get(JournalEntry, release["ledger_entry_id"])
            if (posting is None or posting.source != RELEASE_SOURCE or posting.source_ref != release_key
                    or release["recognized_revenue_minor"] != effect["debit_minor"]):
                raise HTTPException(409, "Prior recognition is contradictory")
        value = {"scope": scope, "order_id": str(order_id), "bank_batch_sha256": bank["sha256"],
                 "signed_dispute_sha256": event.snapshot_sha256, **effect,
                 "corrects_delivery_income": release is not None, "bank_debit_confirmed": False,
                 "available_cash_minor": None, "basis": "STRIPE_CAD_CHARGEBACK" if live else "SYNTHETIC_CHARGEBACK"}
        previous = _read_record(db, key, KIND, scope)
        if previous is not None:
            if any(previous.get(k) != field for k, field in value.items()):
                raise HTTPException(409, "Chargeback evidence changed after accounting")
            entry = db.get(JournalEntry, previous["ledger_entry_id"]) if live else None
            if (live and (entry is None or entry.source != SOURCE or entry.source_ref != key)
                    or not live and previous["ledger_entry_id"] is not None):
                raise HTTPException(409, "Chargeback entry failed integrity")
            return previous
        posted = max(bank["booked_on"], effect["processor_posted_on"], release["posting_date"] if release else "")
        try:
            value["ledger_entry_id"] = _post_correction(
                db, scope, key, date.fromisoformat(posted), effect["debit_minor"], bank, release,
                fee=effect["fee_minor"], source=SOURCE,
            ) if live else None
            digest = artifact_digest(KIND, key, value)
            unique = "STRIPE-DISPUTE-TX-" + artifact_digest(KIND, effect["processor_balance_id"], {"live": live})[:40]
            for reference, payload in ((unique, {"sha256": digest}), (key, {"value": value, "sha256": digest})):
                _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=KIND,
                       message="Independently matched Stripe chargeback", payload=payload)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Chargeback debit already consumed") from None
        return {**value, "sha256": digest}
