"""Read a recorded Stripe payout reversal and independently match its bank debit."""
from datetime import date, datetime, timezone
from decimal import Decimal
import os
import re

from fastapi import HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.services.launch_readiness import require_channel_release
from app.accounting.models import Account, JournalEntry, JournalLine
from app.banking.plaid_transactions import configured_bank_debit
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event, _json
from app.services.specialist_triggers import outcome_scope_key
from app.services.stripe_bank_booking import LEDGER_SOURCE, SETTLEMENT, require_open_period
from app.services.stripe_finance import _provider_object, minor_amount, stripe_id, stripe_readback_client
from app.services.stripe_fulfillment import _read_record

KIND = "STRIPE_PAYOUT_BANK_REVERSAL_MATCHED"
SOURCE = "stripe_bank_reversal"


class BankReversalIn(StrictModel):
    payout_id: str
    reversal_id: str


def _book_reversal(db, original, key, scope, booked_bank, amount, posted):
    if (os.getenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED") != "1"
            or os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(503, "Bank reversal booking is not authorized for this scope")
    linked_id = booked_bank["ledger_entry_id"]
    entry = db.get(JournalEntry, linked_id) if type(linked_id) is int else None
    if entry is None or entry.source != LEDGER_SOURCE or entry.source_ref != original or entry.entry_date > posted:
        raise HTTPException(409, "Original bank posting differs from the reversal")
    require_open_period(db, posted)
    tag = artifact_digest("stripe_booking_scope", original, scope)
    bank, clearing = (db.scalar(select(Account).filter_by(code=os.getenv(env), type="asset", active=True,
                                                         currency="CAD"))
                      for env in ("VALHALLA_STRIPE_BOOK_BANK", "VALHALLA_STRIPE_BOOK_CLEARING"))
    if bank is None or clearing is None or bank.id == clearing.id:
        raise HTTPException(503, "Exact bank and processor clearing accounts are required")
    original_lines = db.scalars(select(JournalLine).where(
        JournalLine.entry_id == entry.id, JournalLine.tag == tag, JournalLine.account_id.in_((bank.id, clearing.id)),
    )).all()
    units = Decimal(amount) / 100
    expected = sorted([(bank.id, units, 0), (clearing.id, units, 0), (clearing.id, 0, units)])
    if sorted((line.account_id, line.debit, line.credit) for line in original_lines) != expected:
        raise HTTPException(409, "Original bank and processor clearing lines did not match")
    if db.scalar(select(JournalEntry.id).filter_by(source=SOURCE, source_ref=key).limit(1)) is not None:
        raise HTTPException(409, "Bank reversal posting already exists without its receipt")
    reversed_entry = JournalEntry(entry_date=posted, memo="Matched Stripe reversal returned to processor clearing",
                                  source=SOURCE, source_ref=key)
    db.add(reversed_entry)
    db.flush()
    proof = artifact_digest("stripe_reversal_scope", key, scope)
    db.add_all([JournalLine(entry_id=reversed_entry.id, account_id=clearing.id, debit=units, credit=0, tag=proof),
                JournalLine(entry_id=reversed_entry.id, account_id=bank.id, debit=0, credit=units, tag=proof)])
    return reversed_entry.id


def record_bank_reversal(db, request, *, live, client, account, destination, bank_debit=configured_bank_debit):
    require_channel_release("accounting_and_bank", live=live)
    if not all(stripe_id(item, "po") for item in (request.payout_id, request.reversal_id)) or request.payout_id == request.reversal_id:
        raise HTTPException(422, "Two distinct native payout identities are required")
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Bank settlement evidence journal unavailable")
    original = "STRIPE-BANK-" + artifact_digest("stripe_bank_batch", request.payout_id,
                                                {"account": account, "live": live})[:40]
    booked = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=original).with_for_update())
    receipt = _json(booked.payload_json, {}) if booked is not None else {}
    value = receipt.get("value") if isinstance(receipt, dict) else None
    expected = "INDEPENDENT_CAD_BANK_READBACK" if live else "SYNTHETIC_BANK_REHEARSAL"
    if (booked is None or booked.event_type != SETTLEMENT or not isinstance(value, dict)
            or value.get("basis") != expected or value.get("payout_id") != request.payout_id
            or receipt.get("sha256") != artifact_digest("stripe_bank_reconciliation", original, value)):
        raise HTTPException(409, "Original independently reconciled bank batch required")
    scope, amount = value["scope"], value["payout_minor"]
    if not isinstance(scope, dict) or booked.legacy_instance_id != scope.get("legacy_instance_id"):
        raise HTTPException(409, "Original bank booking scope differed")
    _provider_object(client, "/v1/account", account, "account")
    from_payout = _provider_object(client, f"/v1/payouts/{request.payout_id}", request.payout_id, "payout")
    reversal = _provider_object(client, f"/v1/payouts/{request.reversal_id}", request.reversal_id, "payout")
    trace = reversal.get("trace_id")
    trace = trace.get("value") if isinstance(trace, dict) else None
    arriving = reversal.get("arrival_date")
    if (not stripe_id(destination, "ba") or not minor_amount(amount) or amount == 0
            or any(p.get("livemode") is not live or p.get("destination") != destination or p.get("currency") != "cad"
                   or p.get("type") != "bank_account" for p in (from_payout, reversal))
            or from_payout.get("reversed_by") != request.reversal_id or from_payout.get("amount") != amount
            or reversal.get("original_payout") != request.payout_id or reversal.get("amount") != -amount
            or reversal.get("status") != "paid" or reversal.get("failure_balance_transaction")
            or not isinstance(trace, str) or not re.fullmatch(r"[A-Za-z0-9-]{4,128}", trace)
            or type(arriving) is not int or not 0 < arriving < 4_102_444_800
            or not stripe_id(reversal.get("balance_transaction"), "txn")):
        raise HTTPException(409, "Exact paid full CAD payout reversal is unavailable")
    balance_id = reversal["balance_transaction"]
    balance = _provider_object(client, f"/v1/balance_transactions/{balance_id}", balance_id, "balance_transaction")
    if (balance.get("source") != request.reversal_id or balance.get("currency") != "cad"
            or balance.get("type") != "payout" or balance.get("status") != "available"
            or (balance.get("amount"), balance.get("net"), balance.get("fee")) != (amount, amount, 0)):
        raise HTTPException(409, "Reversal credit in processor clearing is inconsistent")
    now = datetime.now(timezone.utc).date()
    debit = bank_debit(trace=trace, arrival=datetime.fromtimestamp(arriving, timezone.utc).date(),
                       amount_minor=amount, today=now, live=live, stripe_destination=destination)
    original_bank = value["bank"]
    if (not isinstance(debit, dict) or debit.get("currency") != "CAD"
            or type(debit.get("amount_minor")) is not int or debit["amount_minor"] != amount
            or not re.fullmatch(r"[a-f0-9]{64}", debit.get("transaction_sha256") or "")
            or debit["transaction_sha256"] == original_bank["transaction_sha256"]):
        raise HTTPException(409, "Independent reversal debit differs from the expected new bank movement")
    try:
        posted = date.fromisoformat(debit["posted_on"])
        original_posted = date.fromisoformat(original_bank["posted_on"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(409, "Bank debit or original posting date is invalid") from None
    if not original_posted <= posted <= now:
        raise HTTPException(409, "Reversal debit date differs from the booked sequence")
    key = "STRIPE-BANK-REVERSAL-" + original.removeprefix("STRIPE-BANK-")
    result = {"scope": scope, "original_sha256": receipt["sha256"], "payout_id": request.payout_id,
              "reversal_id": request.reversal_id, "bank_debit": debit, "processor_balance_id": balance_id,
              "bank_debit_verified": live, "available_cash_minor": None,
              "basis": "INDEPENDENT_CAD_BANK_REVERSAL" if live else "SYNTHETIC_BANK_REVERSAL"}
    prior = _read_record(db, key, KIND, scope)
    if prior is not None:
        if any(prior.get(k) != v for k, v in result.items()):
            raise HTTPException(409, "Previously recorded reversal evidence differs")
        posting = db.get(JournalEntry, prior["ledger_entry_id"]) if live else None
        if live and (posting is None or posting.source != SOURCE or posting.source_ref != key):
            raise HTTPException(409, "Recorded reversal journal differs")
        if not live and prior["ledger_entry_id"] is not None:
            raise HTTPException(409, "Synthetic reversal cannot have an accounting entry")
        return prior
    try:
        result["ledger_entry_id"] = _book_reversal(db, original, key, scope, receipt, amount, posted) if live else None
        digest = artifact_digest(KIND, key, result)
        bank_key = "STRIPE-BANK-TX-" + artifact_digest("stripe_bank_credit_key", debit["transaction_sha256"],
                                                       {"live": live})[:48]
        processor_key = "STRIPE-REVERSAL-TX-" + artifact_digest(KIND, balance_id, {"live": live})[:40]
        for event_id, payload in ((bank_key, {"sha256": digest}), (processor_key, {"sha256": digest}),
                                  (key, {"value": result, "sha256": digest})):
            _event(db, event_id=event_id, legacy_instance_id=scope["legacy_instance_id"], event_type=KIND,
                   message="Exact Stripe and independent bank debit reversal", payload=payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Reversal bank or processor evidence already consumed") from None
    return {**result, "sha256": digest}


def configured_bank_reversal(db, request, *, live):
    require_channel_release("accounting_and_bank", live=live)
    with stripe_readback_client(live=live) as (client, account):
        return record_bank_reversal(db, request, live=live, client=client, account=account,
                                    destination=os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID"))
