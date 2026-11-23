"""Reconcile one independent bank deposit to its complete governed payout batch."""
from datetime import date, datetime, timezone
from decimal import Decimal
import os
import re
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, field_validator, model_validator
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounting.models import Account, JournalEntry, JournalLine, Period
from app.banking.plaid_transactions import configured_bank_credit
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_finance import StripeFinancialEvent, StripeOrderBinding
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event, _json
from app.services.stripe_finance import _event_receipt, _provider_object, minor_amount, provider_json, stripe_id, stripe_readback_client
from app.services.stripe_orders import inspect_binding
from app.services.stripe_payout_evidence import EVENT

SETTLEMENT = "STRIPE_BANK_BATCH_RECONCILED"
LEDGER_SOURCE = "stripe_bank_reconciliation"


class BankBatchIn(StrictModel):
    payout_id: str
    order_ids: list[UUID] = Field(default_factory=list, max_length=100)
    invoice_ids: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def bounded_membership(self):
        if not 1 <= len(self.order_ids) + len(self.invoice_ids) <= 100:
            raise ValueError("Provide 1 to 100 exact payout members")
        if len(set(self.invoice_ids)) != len(self.invoice_ids) or not all(stripe_id(x, "in") for x in self.invoice_ids):
            raise ValueError("Provide distinct native invoice identities")
        return self

    @field_validator("payout_id")
    @classmethod
    def native_payout(cls, value):
        if not stripe_id(value, "po"):
            raise ValueError("A native Stripe payout is required")
        return value

    @field_validator("order_ids")
    @classmethod
    def unique_orders(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Order identities must be distinct")
        return sorted(value)


def _payout_receipt(db, order, projection):
    key = "STRIPE-PAYOUT-" + artifact_digest("stripe_order_payout_key", str(order.id),
                                             {"livemode": order.livemode})[:40]
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=key))
    if row is None or row.event_type != EVENT or row.legacy_instance_id != projection["order"]["scope"]["legacy_instance_id"]:
        raise HTTPException(409, "Current scoped processor payout receipt required")
    data = _json(row.payload_json, {})
    if not isinstance(data, dict):
        raise HTTPException(409, "Processor payout receipt failed integrity")
    digest = data.pop("sha256", None)
    if (digest != artifact_digest("stripe_order_payout", key, data)
            or data.get("order_id") != str(order.id) or data.get("order_sha256") != order.binding_sha256
            or data.get("scope") != projection["order"]["scope"]
            or data.get("balance_evidence_sha256") != projection["processor_evidence"]["sha256"]):
        raise HTTPException(409, "Processor payout receipt differs from current order evidence")
    return {**data, "sha256": digest}


def require_open_period(db, posted_on):
    period = db.scalars(select(Period).where(Period.start_date <= posted_on, Period.end_date >= posted_on)
                        .order_by(Period.id).limit(2).with_for_update()).all()
    if len(period) != 1 or period[0].closed:
        raise HTTPException(409, "Exactly one open accounting period must cover the bank posting")


def _journal(db, reference, posted_on, scope, amounts):
    # The chart of accounts is explicitly configured for this authorized receiving scope.
    accounts_env = {
        "bank": ("VALHALLA_STRIPE_BOOK_BANK", "asset"),
        "clearing": ("VALHALLA_STRIPE_BOOK_CLEARING", "asset"),
        "fees": ("VALHALLA_STRIPE_BOOK_FEES", "expense"),
        "obligations": ("VALHALLA_STRIPE_BOOK_OBLIGATIONS", "liability"),
    }
    if any(not inspect(db.connection()).has_table(model.__tablename__) for model in (Account, Period, JournalEntry, JournalLine)):
        raise HTTPException(503, "Canonical accounting tables are unavailable")
    if db.scalar(select(JournalEntry.id).filter_by(source=LEDGER_SOURCE, source_ref=reference).limit(1)) is not None:
        raise HTTPException(409, "Accounting source already exists without matched booking receipt")
    require_open_period(db, posted_on)
    accounts = {}
    for name, (variable, account_type) in accounts_env.items():
        account = db.scalar(select(Account).filter_by(code=os.getenv(variable), type=account_type,
                                                        active=True, currency="CAD"))
        if account is None:
            raise HTTPException(503, "Authorized CAD chart of accounts is incomplete")
        accounts[name] = account.id
    if len(set(accounts.values())) != len(accounts):
        raise HTTPException(409, "Distinct accounting accounts are required")
    bank, fee, gross = amounts
    entry = JournalEntry(entry_date=posted_on, memo="Matched Stripe bank batch and open delivery obligations",
                         source=LEDGER_SOURCE, source_ref=reference)
    db.add(entry)
    db.flush()
    tag = artifact_digest("stripe_booking_scope", reference, scope)
    # Keep the clearing movements explicit while the batch settles to a single bank posting.
    for key, debit, credit in (("clearing", bank, 0), ("fees", fee, 0), ("obligations", 0, gross),
                               ("bank", bank, 0), ("clearing", 0, bank)):
        if debit or credit:
            db.add(JournalLine(entry_id=entry.id, account_id=accounts[key], debit=Decimal(debit) / 100,
                               credit=Decimal(credit) / 100, tag=tag))
    return entry.id


def _payout_failed(db, payout_id, live):
    failed = db.scalar(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == live,
        StripeFinancialEvent.snapshot["kind"].as_string().in_(("payout.failed", "payout.canceled")),
        StripeFinancialEvent.snapshot["object_id"].as_string() == payout_id,
    ).limit(1))
    if failed is not None:
        _event_receipt(failed, True)
    return failed is not None


def reconcile_bank_batch(db: Session, request: BankBatchIn, *, client, account_id, destination, live,
                         bank_credit=configured_bank_credit):
    for model in (StripeOrderBinding, LegacyOrchestrationEvent):
        if not inspect(db.connection()).has_table(model.__tablename__):
            raise HTTPException(503, "Stripe bank reconciliation schema unavailable")
    receipts, projections = [], []
    for order_id in request.order_ids:
        row = db.get(StripeOrderBinding, order_id, with_for_update=True)
        if row is None:
            raise HTTPException(404, "Stripe order binding unavailable")
        projection = inspect_binding(db, order_id, live=live)
        if projection["status"] != "MATCHED_PROCESSOR_EVIDENCE":
            raise HTTPException(409, "Every order requires intact processor evidence without a refund hold")
        receipt = _payout_receipt(db, row, projection)
        if receipt.get("payout_id") != request.payout_id or projection["processor_evidence"]["stripe_account_id"] != account_id:
            raise HTTPException(409, "All orders must match the same scoped processor payout")
        receipts.append(receipt)
        projections.append(projection)
    evidence = [projection["processor_evidence"] for projection in projections]
    scopes = [projection["order"]["scope"] for projection in projections]
    invoices = []
    if request.invoice_ids:
        from app.models.stripe_recurring import StripePaidPeriod, StripeSaaSBinding
        from app.services.stripe_recurring import _period_payout_evidence, _ready

        _ready(db)
        periods = db.scalars(select(StripePaidPeriod).where(StripePaidPeriod.invoice_id.in_(request.invoice_ids))
                             .order_by(StripePaidPeriod.binding_id, StripePaidPeriod.invoice_id)).all()
        if len(periods) != len(request.invoice_ids):
            raise HTTPException(404, "One or more paid invoice periods are unavailable")
        # Hold the binding locks in the same order as the signed refund/dispute intake.
        db.scalars(select(StripeSaaSBinding).where(StripeSaaSBinding.id.in_(
            {period.binding_id for period in periods}
        )).order_by(StripeSaaSBinding.id).with_for_update()).all()
        for period in periods:
            _, _, receipt, capture, prior = _period_payout_evidence(
                db, period.binding_id, period.invoice_id, request.payout_id,
                client=client, destination_id=destination, live=live,
            )
            if prior is None or capture["stripe_account_id"] != account_id:
                raise HTTPException(409, "Every invoice needs existing recurring payout evidence for this account")
            receipts.append(receipt)
            evidence.append(capture)
            scopes.append(receipt["scope"])
            invoices.append({"invoice_id": period.invoice_id, "payout_sha256": receipt["sha256"],
                             "net_minor": capture["net_minor"]})
    scope = scopes[0]
    if any(member_scope != scope for member_scope in scopes):
        raise HTTPException(409, "Mixed-scope payout booking requires explicit allocation")
    _provider_object(client, "/v1/account", account_id, "account")
    payout = _provider_object(client, f"/v1/payouts/{request.payout_id}", request.payout_id, "payout")
    amount, arrival = payout.get("amount"), payout.get("arrival_date")
    trace = payout.get("trace_id")
    trace_value = trace.get("value") if isinstance(trace, dict) else None
    if (payout.get("livemode") is not live or payout.get("destination") != destination
            or not stripe_id(destination, "ba") or payout.get("automatic") is not True or payout.get("method") != "standard"
            or payout.get("type") != "bank_account" or payout.get("currency") != "cad" or payout.get("status") != "paid"
            or payout.get("reconciliation_status") != "completed" or payout.get("reversed_by")
            or payout.get("original_payout") or payout.get("failure_balance_transaction") or payout.get("failure_code")
            or not minor_amount(amount) or amount == 0 or type(arrival) is not int or not 0 < arrival < 4_102_444_800
            or not isinstance(trace_value, str) or not re.fullmatch(r"[A-Za-z0-9-]{4,128}", trace_value)):
        raise HTTPException(409, "Current payout is ineligible or lacks an independently matchable bank trace")
    net = sum(row["net_minor"] for row in evidence)
    gross = sum(row["gross_minor"] for row in evidence)
    fees = sum(row["fee_minor"] for row in evidence)
    if (net != amount or gross != net + fees or len({row["balance_transaction_id"] for row in evidence}) != len(evidence)
            or any(row["currency"] != "cad" for row in evidence)
            or any((r["processor_reported_payout_minor"], r["processor_arrival_on"], r["capture_net_minor"])
                   != (amount, arrival, e["net_minor"]) for r, e in zip(receipts, evidence))):
        raise HTTPException(409, "Exact payout contributions must reconcile to the full payout before booking")
    remote = provider_json(client, "/v1/balance_transactions", params={"payout": request.payout_id, "limit": 100})
    members = remote.get("data")
    if (remote.get("object") != "list" or remote.get("has_more") is not False
            or not isinstance(members, list) or len(members) != len(evidence)
            or any(not isinstance(member, dict) or not stripe_id(member.get("id"), "txn") for member in members)):
        raise HTTPException(409, "Full payout membership is incomplete or includes unsupported adjustments")
    actual = {member["id"]: (member.get("source"), member.get("currency"), member.get("amount"),
                            member.get("fee"), member.get("net")) for member in members}
    expected = {row["balance_transaction_id"]: (row["charge_id"], "cad", row["gross_minor"],
                                                row["fee_minor"], row["net_minor"]) for row in evidence}
    if (actual != expected or any(not minor_amount(member.get(key))
                                  for member in members for key in ("amount", "fee", "net"))):
        raise HTTPException(409, "Payout member values differ from approved order captures")
    bank = bank_credit(trace=trace_value, arrival=datetime.fromtimestamp(arrival, timezone.utc).date(),
                       amount_minor=amount, today=datetime.now(timezone.utc).date(), live=live,
                       stripe_destination=destination)
    if (not isinstance(bank, dict) or bank.get("currency") != "CAD" or
            type(bank.get("amount_minor")) is not int or bank["amount_minor"] != net):
        raise HTTPException(409, "Independent bank credit differs from the exact payout")
    reference = "STRIPE-BANK-" + artifact_digest("stripe_bank_batch", request.payout_id,
                                                  {"account": account_id, "live": live})[:40]
    if _payout_failed(db, request.payout_id, live):
        raise HTTPException(409, "A signed payout failure requires accounting review")
    value = {"source_ref": reference, "scope": scope, "payout_id": request.payout_id,
             "orders": [{"order_id": r["order_id"], "payout_sha256": r["sha256"], "net_minor": e["net_minor"]}
                        for r, e in zip(receipts, evidence) if "order_id" in r],
             "bank": bank, "gross_customer_obligation_minor": gross, "processor_fee_minor": fees,
             "payout_minor": net, "basis": "INDEPENDENT_CAD_BANK_READBACK" if live else "SYNTHETIC_BANK_REHEARSAL",
             "bank_settlement_verified": live, "available_cash_minor": None, "fulfillment_authorized": False}
    if invoices:
        value["invoices"] = invoices
    digest = artifact_digest("stripe_bank_reconciliation", reference, value)
    previous = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=reference))
    if previous is not None:
        recorded = _json(previous.payload_json, {})
        if (previous.event_type != SETTLEMENT or previous.legacy_instance_id != scope["legacy_instance_id"]
                or not isinstance(recorded, dict) or recorded.get("value") != value or recorded.get("sha256") != digest):
            raise HTTPException(409, "Payout or bank evidence changed after reconciliation")
        stored_id = recorded.get("ledger_entry_id")
        if live:
            entry = db.get(JournalEntry, stored_id) if type(stored_id) is int else None
            if entry is None or entry.source != LEDGER_SOURCE or entry.source_ref != reference:
                raise HTTPException(409, "Stored accounting entry differs from reconciled evidence")
        elif stored_id is not None:
            raise HTTPException(409, "Sandbox reconciliation cannot have an accounting entry")
        return recorded
    check = os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE")
    from app.services.specialist_triggers import outcome_scope_key

    journal_id = None
    try:
        if live:
            if os.getenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED") != "1" or check != outcome_scope_key(scope):
                raise HTTPException(503, "Bank ledger booking is not authorized for this scope")
            journal_id = _journal(db, reference, date.fromisoformat(bank["posted_on"]), scope, (net, fees, gross))
        result = {"value": value, "sha256": digest, "ledger_entry_id": journal_id}
        consumed_ids = ["STRIPE-BANK-TX-" + artifact_digest("stripe_bank_credit_key", bank["transaction_sha256"],
                                                              {"live": live})[:48],
                        *("STRIPE-BANK-ORDER-" + str(order_id) for order_id in request.order_ids),
                        *("STRIPE-BANK-INVOICE-" + artifact_digest("stripe_bank_invoice_key", member["invoice_id"],
                                                                  {"live": live})[:40] for member in invoices)]
        for identity in consumed_ids:
            _event(db, event_id=identity, legacy_instance_id=scope["legacy_instance_id"], event_type=SETTLEMENT,
                   message="Bank batch evidence consumed", payload={"bundle": reference, "sha256": digest})
        _event(db, event_id=reference, legacy_instance_id=scope["legacy_instance_id"], event_type=SETTLEMENT,
               message="Stripe bank batch reconciled", payload=result)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bank transaction, payout, or order already reconciled; reload the exact batch") from None
    return result


def configured_bank_batch(db, request, *, live):
    destination = os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID")
    with stripe_readback_client(live=live) as (client, account_id):
        return reconcile_bank_batch(db, request, client=client, account_id=account_id, destination=destination, live=live)



def bank_batch_summary(db: Session, order_id: UUID, projection: dict, *, live: bool):
    journal = LegacyOrchestrationEvent
    if not inspect(db.connection()).has_table(journal.__tablename__):
        return None
    scope = projection["order"]["scope"]
    claim = db.scalar(select(journal).filter_by(event_id=f"STRIPE-BANK-ORDER-{order_id}"))
    if claim is None:
        return None
    index = _json(claim.payload_json, {})
    if (claim.event_type != SETTLEMENT or claim.legacy_instance_id != scope["legacy_instance_id"]
            or not isinstance(index, dict) or not isinstance(index.get("bundle"), str)):
        raise HTTPException(409, "Bank order booking index differs from its scope")
    entry = db.scalar(select(journal).filter_by(event_id=index["bundle"]))
    if entry is None or entry.event_type != SETTLEMENT or entry.legacy_instance_id != scope["legacy_instance_id"]:
        raise HTTPException(409, "Bank booking receipt unavailable")
    receipt = _json(entry.payload_json, {})
    value = receipt.get("value") if isinstance(receipt, dict) else None
    expected_basis = "INDEPENDENT_CAD_BANK_READBACK" if live else "SYNTHETIC_BANK_REHEARSAL"
    if (not isinstance(value, dict) or value.get("scope") != scope or value.get("basis") != expected_basis
            or receipt.get("sha256") != index.get("sha256")
            or receipt["sha256"] != artifact_digest("stripe_bank_reconciliation", entry.event_id, value)):
        raise HTTPException(409, "Bank booking receipt integrity failed")
    member = next((order for order in value["orders"] if order["order_id"] == str(order_id)), None)
    if member is None:
        raise HTTPException(409, "Bank booking receipt does not include this order")
    ledger_id = receipt.get("ledger_entry_id")
    if live:
        account_entry = db.get(JournalEntry, ledger_id) if type(ledger_id) is int else None
        if account_entry is None or account_entry.source != LEDGER_SOURCE or account_entry.source_ref != entry.event_id:
            raise HTTPException(409, "Matched accounting entry is unavailable")
    elif ledger_id is not None:
        raise HTTPException(409, "Synthetic evidence cannot have a ledger posting")
    held = projection["status"] != "MATCHED_PROCESSOR_EVIDENCE" or _payout_failed(db, value["payout_id"], live)
    return {
        "basis": expected_basis, "status": "CORRECTION_REVIEW_REQUIRED" if held else "RECONCILIATION_RECORDED",
        "currency": "CAD", "batch_minor": value["payout_minor"], "order_contribution_minor": member["net_minor"],
        "payout_id": value["payout_id"],
        "booked_on": value["bank"]["posted_on"], "ledger_entry_id": ledger_id, "available_cash_minor": None,
        "batch_liability_minor": value["gross_customer_obligation_minor"], "sha256": receipt["sha256"],
    }


def scoped_bank_blockers(db: Session, scope: dict, *, live: bool) -> set[str]:
    """Hold scoped reallocations when a booked payout needs independent correction."""
    journal = LegacyOrchestrationEvent
    if not inspect(db.connection()).has_table(journal.__tablename__):
        return set()
    entries = db.scalars(select(journal).where(
        journal.event_type == SETTLEMENT, journal.legacy_instance_id == scope["legacy_instance_id"],
        journal.event_id.startswith("STRIPE-BANK-"), ~journal.event_id.startswith("STRIPE-BANK-ORDER-"),
        ~journal.event_id.startswith("STRIPE-BANK-TX-"), ~journal.event_id.startswith("STRIPE-BANK-INVOICE-"),
    ).execution_options(yield_per=100))
    expected_basis = "INDEPENDENT_CAD_BANK_READBACK" if live else "SYNTHETIC_BANK_REHEARSAL"
    blockers = set()
    for entry in entries:
        receipt = _json(entry.payload_json, {})
        value = receipt.get("value") if isinstance(receipt, dict) else None
        if not isinstance(value, dict) or not isinstance(value.get("scope"), dict):
            blockers.add("STRIPE_BANK_EVIDENCE_CONFLICT")
            continue
        if value["scope"] != scope:
            continue
        if receipt.get("sha256") != artifact_digest("stripe_bank_reconciliation", entry.event_id, value):
            blockers.add("STRIPE_BANK_EVIDENCE_CONFLICT")
            continue
        if value.get("basis") != expected_basis:
            continue
        try:
            if _payout_failed(db, value["payout_id"], live):
                blockers.add("STRIPE_BANK_CORRECTION_REQUIRED")
            if value.get("invoices"):
                from app.models.stripe_recurring import StripePaidPeriod
                from app.services.stripe_recurring import _binding, _period_value, _reversed

                for member in value["invoices"]:
                    period = db.get(StripePaidPeriod, member["invoice_id"])
                    if period is None:
                        raise HTTPException(409, "Reconciled paid period missing")
                    binding, data, _ = _binding(db, period.binding_id, live)
                    if data["scope"] != scope:
                        raise HTTPException(409, "Reconciled invoice escaped operating scope")
                    if _reversed(db, binding, _period_value(binding, period)):
                        blockers.add("STRIPE_BANK_CORRECTION_REQUIRED")
            for member in value["orders"]:
                order_id = UUID(member["order_id"])
                projection = inspect_binding(db, order_id, live=live)
                summary = bank_batch_summary(db, order_id, projection, live=live)
                if summary is None:
                    blockers.add("STRIPE_BANK_EVIDENCE_CONFLICT")
                elif summary["status"] == "CORRECTION_REVIEW_REQUIRED":
                    blockers.add("STRIPE_BANK_CORRECTION_REQUIRED")
        except (HTTPException, ValueError, KeyError, TypeError):
            blockers.add("STRIPE_BANK_EVIDENCE_CONFLICT")
    return blockers
