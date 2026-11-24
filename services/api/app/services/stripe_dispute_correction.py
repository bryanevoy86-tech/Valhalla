"""Book bounded, independently verified terminal CAD chargebacks."""
from datetime import date, datetime, timezone
from decimal import Decimal
import os

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.services.launch_readiness import require_channel_release
from app.accounting.models import Account, JournalEntry, JournalLine
from app.integrations.stripe import ACTIVE_DISPUTE_STATUSES
from app.loki.evidence import artifact_digest
from app.models.stripe_finance import StripeFinancialEvent
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event
from app.services.specialist_triggers import outcome_scope_key
from app.services.stripe_bank_booking import _payout_failed, bank_batch_summary, require_open_period
from app.services.stripe_finance import (
    _event_receipt, _provider_object, minor_amount, stripe_id, stripe_readback_client,
)
from app.services.stripe_fulfillment import _locked_order, _read_record
from app.services.stripe_orders import inspect_binding
from app.services.stripe_refund_correction import _post_correction
from app.services.stripe_revenue_release import RELEASE, SOURCE as RELEASE_SOURCE

KIND = "STRIPE_FINAL_CHARGEBACK_PROCESSOR_CORRECTION"
SOURCE = "stripe_dispute_processor_correction"
REINSTATEMENT = "STRIPE_DISPUTE_PROCESSOR_REINSTATEMENT"
REINSTATEMENT_SOURCE = "stripe_dispute_processor_reinstatement"


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
    return _debit_transaction(client, members[0]["id"], dispute_id, charge_id, disputed, now)


def _debit_transaction(client, txn, dispute_id, charge_id, disputed, now):
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
    require_channel_release("accounting_and_bank", live=live)
    with stripe_readback_client(live=live) as (client, account):
        _, binding = _locked_order(db, order_id, live)
        if not stripe_id(request.signed_event_id, "evt"):
            raise HTTPException(422, "Native Stripe event identity required")
        event = db.get(StripeFinancialEvent, request.signed_event_id)
        if account != binding["stripe_account_id"] or event is None or event.livemode is not live:
            raise HTTPException(409, "Scoped Stripe dispute evidence is unavailable")
        _event_receipt(event, True)
        projection = inspect_binding(db, order_id, live=live, include_held_evidence=True)
        won = _is_won(event)
        bank = bank_batch_summary(db, order_id, projection, live=live, include_order_hold=not won, lock=won)
        if bank is None or _payout_failed(db, bank["payout_id"], live) or projection["processor_evidence"] is None:
            raise HTTPException(409, "Original batch and capture evidence are required")
        scope = binding["scope"]
        charge_id = projection["processor_evidence"]["charge_id"]
        _deny_prior_refund(db, charge_id, live)
        key = f"STRIPE-CHARGEBACK-{order_id}"
        identity = {"order_id": str(order_id)}
        if won:
            if bank["status"] != "RECONCILIATION_RECORDED":
                raise HTTPException(409, "A separate payout correction requires review")
            return _reinstate(db, client, event, binding, charge_id, bank, key, identity, live=live)
        _deny_superseded_loss(db, event)
        effect = _debit(client, event.snapshot, binding, charge_id, datetime.now(timezone.utc))
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
    require_channel_release("accounting_and_bank", live=live)
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
        reference = artifact_digest(ACK, invoice_id, {"live": live})[:32]
        key = f"STRIPE-SERVICE-CHARGEBACK-{local_id}-{reference}"
        identity = {"subscription_id": local_id, "invoice_id": invoice_id, "paid_period_sha256": period.evidence_sha256}
        if _is_won(event):
            return _reinstate(db, client, event, {**financial, "scope": scope}, paid["charge_id"], bank,
                              key, identity, live=live)
        _deny_superseded_loss(db, event)
        effect = _debit(client, event.snapshot, financial, paid["charge_id"], datetime.now(timezone.utc))
        release_key = f"STRIPE-SERVICE-REVENUE-{local_id}-{reference}"
        release = _read_record(db, release_key, SERVICE_RELEASE, scope)
        if release is not None and (release["paid_period_sha256"] != period.evidence_sha256
                                    or release["batch_sha256"] != bank["sha256"]):
            raise HTTPException(409, "Prior service recognition did not match this invoice settlement")
        value = {"scope": scope, "subscription_id": local_id, "invoice_id": invoice_id,
                 "paid_period_sha256": period.evidence_sha256, "bank_batch_sha256": bank["sha256"],
                 "signed_dispute_sha256": event.snapshot_sha256, **effect,
                 "corrects_delivery_income": release is not None, "bank_debit_confirmed": False,
                 "available_cash_minor": None, "basis": "STRIPE_CAD_CHARGEBACK" if live else "SYNTHETIC_CHARGEBACK"}
        return _record_chargeback(
            db, key, value, bank, release_key, release, captured_minor=paid["captured_minor"], live=live,
        )


def _is_won(event):
    return (event.snapshot.get("native_status") == "won"
            and event.snapshot["kind"] in {"charge.dispute.closed", "charge.dispute.funds_reinstated"})


def _reinstatement_credit(client, snapshot, binding, charge_id, original, now):
    dispute_id, principal = original["dispute_id"], original["debit_minor"]
    expected = (charge_id, binding["payment_intent_id"], "cad", principal)
    if ((snapshot.get("charge_id"), snapshot.get("payment_intent_id"), snapshot.get("currency"),
         snapshot.get("amount_minor")) != expected or snapshot["object_id"] != dispute_id):
        raise HTTPException(409, "Signed win did not match the original chargeback")
    _provider_object(client, "/v1/account", binding["stripe_account_id"], "account")
    charge = _provider_object(client, f"/v1/charges/{charge_id}", charge_id, "charge")
    if (charge.get("livemode") is not binding["livemode"] or charge.get("amount_refunded") != 0
            or charge.get("payment_intent") != binding["payment_intent_id"] or charge.get("currency") != "cad"
            or charge.get("amount_captured") != binding["amount_minor"]):
        raise HTTPException(409, "Original charge no longer reconciles")
    dispute = _provider_object(client, f"/v1/disputes/{dispute_id}", dispute_id, "dispute")
    members = dispute.get("balance_transactions")
    if (dispute.get("livemode") is not binding["livemode"] or dispute.get("status") != "won"
            or not minor_amount(dispute.get("amount"))
            or (dispute.get("charge"), dispute.get("payment_intent"), dispute.get("currency"),
                dispute.get("amount")) != expected or not isinstance(members, list) or len(members) != 2
            or not all(isinstance(member, dict) and stripe_id(member.get("id"), "txn") for member in members)):
        raise HTTPException(409, "An exact won dispute with one debit and one reinstatement is required")
    debit_id = original["processor_balance_id"]
    members = {member["id"] for member in members}
    if len(members) != 2 or debit_id not in members:
        raise HTTPException(409, "Original debit is missing from the dispute")
    debit = _debit_transaction(client, debit_id, dispute_id, charge_id, principal, now)
    if any(original.get(field) != value for field, value in debit.items()):
        raise HTTPException(409, "Original debit changed")
    credit_id = next(iter(members - {debit_id}))
    credit = _provider_object(client, f"/v1/balance_transactions/{credit_id}", credit_id, "balance_transaction")
    fee, available_on = credit.get("fee"), credit.get("available_on")
    if (credit.get("source") not in {dispute_id, charge_id} or credit.get("currency") != "cad"
            or credit.get("type") != "adjustment" or credit.get("reporting_category") != "dispute_reversal"
            or credit.get("status") != "available" or type(credit.get("amount")) is not int
            or credit["amount"] != principal or type(fee) is not int or not -original["fee_minor"] <= fee <= 0
            or type(credit.get("net")) is not int or credit["net"] != principal - fee
            or type(available_on) is not int or not 0 < available_on <= int(now.timestamp())):
        raise HTTPException(409, "Processor reinstatement principal, fees or clearing availability did not reconcile")
    posted = datetime.fromtimestamp(available_on, timezone.utc).date().isoformat()
    if posted < original["processor_posted_on"]:
        raise HTTPException(409, "Reinstatement predates its original debit")
    return {"credit_balance_id": credit_id, "principal_minor": principal, "returned_fee_minor": -fee,
            "processor_posted_on": posted}


def _post_reinstatement(db, key, original_key, original, value):
    scope = value["scope"]
    if (os.getenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED") != "1"
            or os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(503, "Processor reinstatement is not authorized for this scope")
    prior = db.get(JournalEntry, original["ledger_entry_id"])
    if prior is None or prior.source != SOURCE or prior.source_ref != original_key:
        raise HTTPException(409, "Original chargeback posting failed integrity")
    posted = max(prior.entry_date, date.fromisoformat(value["processor_posted_on"]))
    require_open_period(db, posted)
    principal = Decimal(original["debit_minor"]) / 100
    chargeback_fee = Decimal(original["fee_minor"]) / 100
    returned_fee = Decimal(value["returned_fee_minor"]) / 100
    offset = ("REFUND_CONTRA_INCOME", "income") if original["corrects_delivery_income"] else ("OBLIGATIONS", "liability")
    account_spec = [("CLEARING", "asset"), offset]
    if chargeback_fee:
        account_spec.append(("FEES", "expense"))
    accounts = [db.scalar(select(Account).filter_by(
        code=os.getenv(f"VALHALLA_STRIPE_BOOK_{code}"), type=kind, active=True, currency="CAD",
    )) for code, kind in account_spec]
    if any(account is None for account in accounts):
        raise HTTPException(503, "Approved reinstatement accounts are unavailable")
    clearing, offset_account, *expense = [account.id for account in accounts]
    expected = [(clearing, 0, principal + chargeback_fee), (offset_account, principal, 0)]
    if expense:
        expected.append((expense[0], chargeback_fee, 0))
    lines = db.scalars(select(JournalLine).filter_by(entry_id=prior.id)).all()
    old_tag = artifact_digest("stripe_refund_scope", original_key, scope)
    if any(line.tag != old_tag for line in lines) or sorted(
        (line.account_id, line.debit, line.credit) for line in lines
    ) != sorted(expected):
        raise HTTPException(409, "Original chargeback lines failed integrity")
    if db.scalar(select(JournalEntry.id).filter_by(source=REINSTATEMENT_SOURCE, source_ref=key).limit(1)) is not None:
        raise HTTPException(409, "Reinstatement posting exists without its evidence receipt")
    entry = JournalEntry(entry_date=posted, memo="Independently matched Stripe dispute reinstatement",
                         source=REINSTATEMENT_SOURCE, source_ref=key)
    db.add(entry)
    db.flush()
    tag = artifact_digest("stripe_reinstatement_scope", key, scope)
    inverse = [(clearing, principal + returned_fee, 0), (offset_account, 0, principal)]
    if returned_fee:
        inverse.append((expense[0], 0, returned_fee))
    db.add_all([JournalLine(entry_id=entry.id, account_id=account, debit=debit, credit=credit, tag=tag)
                for account, debit, credit in inverse])
    return entry.id


def _reinstate(db, client, event, binding, charge_id, bank, original_key, identity, *, live):
    scope = binding["scope"]
    original = _read_record(db, original_key, KIND, scope)
    if (original is None or original["bank_batch_sha256"] != bank["sha256"]
            or any(original.get(field) != value for field, value in identity.items())
            or (not live and original["ledger_entry_id"] is not None)):
        raise HTTPException(409, "The exact original chargeback and unchanged settlement are required")
    win_at = event.snapshot.get("provider_created_at")
    if type(win_at) is not int:
        raise HTTPException(409, "A signed Stripe win timestamp is required")
    snapshot = StripeFinancialEvent.snapshot
    conflicting = db.scalars(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == live,
        snapshot["object_id"].as_string() == original["dispute_id"],
        snapshot["charge_id"].as_string() == charge_id,
        snapshot["amount_minor"].as_integer() == original["debit_minor"],
        snapshot["native_status"].as_string().in_(ACTIVE_DISPUTE_STATUSES | {"lost"}),
    )).all()
    for candidate in conflicting:
        _event_receipt(candidate, True)
        observed_at = candidate.snapshot.get("provider_created_at")
        if observed_at is None:
            if candidate.snapshot_sha256 == original["signed_dispute_sha256"]:
                continue
            raise HTTPException(409, "Conflicting dispute status cannot be ordered")
        if observed_at >= win_at:
            raise HTTPException(409, "The signed dispute win is stale or contradictory")
    effect = _reinstatement_credit(client, event.snapshot, binding, charge_id, original, datetime.now(timezone.utc))
    key = "STRIPE-WON-" + artifact_digest(REINSTATEMENT, original_key, {"live": live})[:40]
    value = {"scope": scope, **identity, **effect, "dispute_id": original["dispute_id"],
             "original_chargeback_sha256": original["sha256"], "bank_batch_sha256": bank["sha256"],
             "basis": "STRIPE_CAD_REINSTATEMENT" if live else "SYNTHETIC_REINSTATEMENT",
             "bank_credit_confirmed": False, "available_cash_minor": None, "cash_hold_released": False}
    previous = _read_record(db, key, REINSTATEMENT, scope)
    if previous is not None:
        entry = db.get(JournalEntry, previous["ledger_entry_id"]) if live else None
        if (any(previous.get(field) != detail for field, detail in value.items())
                or (live and (entry is None or entry.source != REINSTATEMENT_SOURCE or entry.source_ref != key))
                or (not live and previous["ledger_entry_id"] is not None)):
            raise HTTPException(409, "Reinstatement differs from its recorded correction")
        return previous
    value["signed_win_sha256"] = event.snapshot_sha256
    try:
        value["ledger_entry_id"] = _post_reinstatement(db, key, original_key, original, value) if live else None
        digest = artifact_digest(REINSTATEMENT, key, value)
        unique = "STRIPE-DISPUTE-TX-" + artifact_digest(KIND, effect["credit_balance_id"], {"live": live})[:40]
        for reference, payload in ((unique, {"sha256": digest}), (key, {"value": value, "sha256": digest})):
            _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=REINSTATEMENT,
                   message="Independently matched Stripe dispute reinstatement", payload=payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Reinstatement credit already consumed") from None
    return {**value, "sha256": digest}
