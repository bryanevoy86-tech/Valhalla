"""Statement arithmetic. The private fixture journal has no payment or vault writer."""
from datetime import date, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, ValidationError, model_validator
from sqlalchemy import inspect, select, update

from app.loki.evidence import artifact_digest
from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport
from app.schemas.economic_control import Currency, Money, Net, Reference
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.specialist_triggers import outcome_scope_key


class Entry(StrictModel):
    external_ref: Reference
    posted_on: date
    amount_minor: Net
    category: Literal["REVENUE", "EXPENSE", "COMPENSATION", "TRANSFER", "ASSET_RECOVERY", "UNCLASSIFIED"]


class StatementFixture(StrictModel):
    id: UUID
    scope: MarketScope
    source_id: Reference
    account_ref: Reference
    purpose: Literal["BUSINESS", "HOUSEHOLD", "OPERATING_RESERVE"]
    currency: Currency
    start: date
    end: date
    opening_minor: Net
    closing_minor: Net
    outstanding_liabilities_minor: Money
    expense_budget_minor: Money
    entries: list[Entry] = Field(max_length=500)
    basis: Literal["LOCAL_STATEMENT_FIXTURE"]

    @model_validator(mode="after")
    def net_reconciliation(self):
        if not self.start <= self.end <= self.start + timedelta(days=366):
            raise ValueError("Invalid statement period")
        if any(not self.start <= row.posted_on <= self.end or row.amount_minor == 0 for row in self.entries):
            raise ValueError("Entries must be nonzero and within the statement period")
        if len({row.external_ref.casefold() for row in self.entries}) != len(self.entries):
            raise ValueError("Duplicate source transaction references")
        if self.opening_minor + sum(row.amount_minor for row in self.entries) != self.closing_minor:
            raise ValueError("Opening balance and entries do not reconcile to closing balance")
        return self


def statement_ready(db):
    schema = inspect(db.connection())
    return all(schema.has_table(model.__tablename__)
               for model in (StatementAccount, StatementImport, StatementEntry))


def payload_for(row):
    if row.digest != artifact_digest("local_statement_fixture", str(row.id), row.payload):
        raise HTTPException(409, "Statement fixture integrity failed")
    return StatementFixture.model_validate(row.payload)


def verify_statement_claim(db, scope: dict, claim: dict) -> dict:
    """A reconciled fixture can support its stated balance, never actual available funds."""
    from uuid import UUID

    if (set(claim) != {"basis", "statement_id", "sha256", "closing_minor"}
            or not isinstance(claim["statement_id"], str)
            or not isinstance(claim["sha256"], str)
            or len(claim["sha256"]) != 64
            or type(claim["closing_minor"]) is not int):
        raise HTTPException(422, "Invalid Mimir statement claim")
    try:
        statement_id = UUID(claim["statement_id"])
    except ValueError:
        raise HTTPException(422, "Invalid statement ID") from None
    if not statement_ready(db):
        raise HTTPException(503, "Statement fixture schema unavailable")
    row = db.get(StatementImport, statement_id)
    if row is None or row.digest != claim["sha256"]:
        raise HTTPException(409, "Mimir statement claim lacks matching scoped evidence")
    document = payload_for(row)
    if (document.scope.model_dump() != scope or document.purpose != "BUSINESS"
            or document.basis != claim["basis"] or document.closing_minor != claim["closing_minor"]):
        raise HTTPException(409, "Mimir statement claim lacks matching scoped evidence")
    return {**claim, "statement_id": str(statement_id), "evidence_scope": "LOCAL_STATEMENT_FIXTURE_ONLY",
            "actual_accessible_funds_minor": None}


def summary(request):
    expense = -sum(min(0, row.amount_minor) for row in request.entries if row.category == "EXPENSE")
    compensation = sum(row.amount_minor for row in request.entries if row.category == "COMPENSATION")
    unclassified = sum(abs(row.amount_minor) for row in request.entries if row.category == "UNCLASSIFIED")
    return {
        "id": request.id, "purpose": request.purpose, "currency": request.currency,
        "opening_minor": request.opening_minor, "closing_minor": request.closing_minor,
        "outstanding_liabilities_minor": request.outstanding_liabilities_minor,
        "expense_minor": expense, "compensation_net_minor": compensation,
        "budget_variance_minor": request.expense_budget_minor - expense, "unclassified_minor": unclassified,
        "protected_balance_minor": max(0, request.closing_minor) if request.purpose != "BUSINESS" else 0,
        "entry_count": len(request.entries), "basis": request.basis,
        "actual_accessible_funds_minor": None, "external_authority": False,
    }


def append_statement(db, request, today):
    scope = request.scope.model_dump()
    binding = outcome_scope_key(scope)
    if request.end > today:
        raise HTTPException(422, "Statement periods must end by today")
    document = request.model_dump(mode="json")
    digest = artifact_digest("local_statement_fixture", str(request.id), document)
    account_key = artifact_digest("statement_source_account", request.source_id.casefold(),
                                  request.account_ref.casefold())
    # Reserve the account's write lock before looking at continuity or duplicates.
    db.execute(update(StatementAccount).where(StatementAccount.account_key == account_key)
               .values(head_id=StatementAccount.head_id))
    account = db.get(StatementAccount, account_key)
    if account is None:
        account = StatementAccount(account_key=account_key, scope_key=binding,
                                   currency=request.currency, purpose=request.purpose)
        db.add(account)
    elif (account.scope_key, account.currency, account.purpose) != (binding, request.currency, request.purpose):
        raise HTTPException(409, "Statement account scope, purpose and currency are immutable")
    existing = db.get(StatementImport, request.id)
    if existing is not None:
        prior = payload_for(existing)
        if existing.digest != digest or existing.account_key != account_key:
            raise HTTPException(409, "Statement identity already used")
        return {**summary(prior), "sha256": digest}
    if account.head_id is not None:
        head = db.get(StatementImport, account.head_id)
        if head is None or head.account_key != account_key:
            raise HTTPException(409, "Statement account continuity unavailable")
        prior = payload_for(head)
        if prior.end + timedelta(days=1) != request.start or prior.closing_minor != request.opening_minor:
            raise HTTPException(409, "Statement periods must be contiguous and balances must carry forward")
    for entry in request.entries:
        key = artifact_digest("statement_transaction", account_key, entry.external_ref.casefold())
        db.add(StatementEntry(key=key, statement_id=request.id))
    db.add(StatementImport(id=request.id, account_key=account_key, period_end=request.end,
                           digest=digest, payload=document))
    account.head_id = request.id
    return {**summary(request), "sha256": digest}

def observe_statement_heads(db, scope: dict, *, purpose="BUSINESS", detailed=False) -> dict:
    """Sample current scoped business fixture heads for specialist reconciliation."""
    if not statement_ready(db):
        return {"status": "UNAVAILABLE", "actual_accessible_funds_minor": None}
    account = StatementAccount
    binding = outcome_scope_key(scope)
    rows = db.scalars(select(account).where(account.scope_key == binding, account.purpose == purpose)
                      .order_by(account.account_key).limit(21)).all()
    observations = []
    for ledger in rows[:20]:
        reference = {"account_key": ledger.account_key, "statement_id": str(ledger.head_id) if ledger.head_id else None}
        statement = db.get(StatementImport, ledger.head_id) if ledger.head_id is not None else None
        try:
            if statement is None or statement.account_key != ledger.account_key:
                raise HTTPException(409, "Statement head unavailable")
            snapshot = payload_for(statement)
            if (snapshot.scope.model_dump() != scope or snapshot.currency != ledger.currency
                    or snapshot.purpose != ledger.purpose or snapshot.end != statement.period_end):
                raise HTTPException(409, "Statement head context mismatch")
            observations.append({**reference, "status": "MATCHED_FIXTURE", "sha256": statement.digest,
                                 "currency": snapshot.currency, "closing_minor": snapshot.closing_minor,
                                 "outstanding_liabilities_minor": snapshot.outstanding_liabilities_minor})
            if detailed:
                activity = summary(snapshot)
                observations[-1].update({key: activity[key] for key in (
                    "expense_minor", "compensation_net_minor", "budget_variance_minor", "protected_balance_minor",
                )})
        except (HTTPException, ValidationError):
            observations.append({**reference, "status": "EVIDENCE_CONFLICT"})
    return {"status": "FIXTURE_SAMPLE" if rows else "NO_SCOPED_FIXTURES",
            "accounts": observations, "truncated": len(rows) > 20,
            "actual_accessible_funds_minor": None}
