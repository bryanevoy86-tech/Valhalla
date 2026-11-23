"""Read-only reconciliation of one CAD bank balance and a signed scoped cash close."""
from datetime import datetime, timedelta
import json
import os
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from pydantic import AwareDatetime, Field
from sqlalchemy import inspect, select

from app.accounting.models import JournalEntry, JournalLine
from app.loki.evidence import artifact_digest
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.specialist_triggers import outcome_scope_key
from app.services.wealth_scenario import AllocationPreferences, allocation_waterfall

Protection = Literal["delivery_obligations", "deferred_revenue", "refund_disputes", "tax_and_other_liabilities",
                     "restricted_funds", "committed_expenses", "operating_reserve", "emergency_reserve"]
REQUIRED_PROTECTIONS = {"delivery_obligations", "deferred_revenue", "refund_disputes", "tax_and_other_liabilities",
                        "restricted_funds", "committed_expenses", "operating_reserve", "emergency_reserve"}
KIND = "scoped_cad_cash_close_v1"


class CashProtectionIn(StrictModel):
    category: Protection
    ledger_item_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    amount_minor: int = Field(gt=0, le=999_999_999_999, strict=True)
    already_reflected_in_bank_available: bool = Field(strict=True)


class CashCloseIn(StrictModel):
    scope: MarketScope
    signer_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,60}$")
    signature: str = Field(pattern=r"^[a-f0-9]{128}$")
    issued_at: AwareDatetime
    account_reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ledger_snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    journal_head: int = Field(gt=0, strict=True)
    currency: Literal["CAD"]
    evidence_class: Literal["SYNTHETIC", "INDEPENDENT_ACCOUNTING_REVIEW"]
    bank_current_minor: int = Field(ge=-999_999_999_999, le=999_999_999_999, strict=True)
    bank_available_minor: int = Field(ge=-999_999_999_999, le=999_999_999_999, strict=True)
    reviewed_categories: list[Protection] = Field(min_length=8, max_length=8)
    protections: list[CashProtectionIn] = Field(max_length=300)
    retained_distributable_profit_minor: int = Field(ge=0, le=999_999_999_999, strict=True)


class CashPositionRequest(StrictModel):
    signed_close: CashCloseIn
    allocation_preferences: AllocationPreferences | None = None


def cash_close_message(packet):
    return artifact_digest(KIND, packet.signer_id, packet.model_dump(mode="json", exclude={"signature"})).encode("ascii")


def verify_cash_close(db, packet, *, live, now):
    scope = outcome_scope_key(packet.scope.model_dump())
    if packet.evidence_class != ("INDEPENDENT_ACCOUNTING_REVIEW" if live else "SYNTHETIC"):
        raise HTTPException(409, "Cash close evidence class differs from the runtime lane")
    if not now - timedelta(minutes=15) <= packet.issued_at <= now:
        raise HTTPException(409, "Signed cash close is stale or dated in the future")
    if set(packet.reviewed_categories) != REQUIRED_PROTECTIONS:
        raise HTTPException(409, "The signed cash close must review every protected category")
    if len({item.ledger_item_sha256 for item in packet.protections}) != len(packet.protections):
        raise HTTPException(409, "Repeated liability, restriction or reserve evidence")
    try:
        enrollment = json.loads(os.getenv("VALHALLA_TREASURY_CASH_ATTESTATION_KEYS", "{}"))[packet.signer_id]
        if (enrollment["scope_sha256"] != scope or enrollment["account_sha256"] != packet.account_reference_sha256
                or enrollment["evidence_class"] != packet.evidence_class):
            raise ValueError
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(enrollment["public_key_hex"]))
        key.verify(bytes.fromhex(packet.signature), cash_close_message(packet))
    except (KeyError, TypeError, ValueError, InvalidSignature):
        raise HTTPException(409, "Exact scoped independent cash close signature required") from None
    verify_journal_head(db, packet)


def journal_snapshot(db):
    schema = inspect(db.connection())
    if not all(schema.has_table(model.__tablename__) for model in (JournalEntry, JournalLine)):
        raise HTTPException(503, "Canonical accounting journal is unavailable")
    entries = db.scalars(select(JournalEntry).order_by(JournalEntry.id).limit(5001).execution_options(populate_existing=True)).all()
    lines = db.scalars(select(JournalLine).order_by(JournalLine.id).limit(20001).execution_options(populate_existing=True)).all()
    if not entries or len(entries) > 5000 or len(lines) > 20000:
        raise HTTPException(409, "Exact cash close requires a nonempty, bounded accounting journal")
    entry_ids = {entry.id for entry in entries}
    net_by_entry = {}
    for line in lines:
        if (line.entry_id not in entry_ids or line.account_id is None or not line.debit.is_finite()
                or not line.credit.is_finite() or min(line.debit, line.credit) < 0
                or (line.debit > 0) == (line.credit > 0)):
            raise HTTPException(409, "Accounting journal contains an invalid line")
        net_by_entry[line.entry_id] = net_by_entry.get(line.entry_id, 0) + line.debit - line.credit
    if set(net_by_entry) != entry_ids or any(net_by_entry.values()):
        raise HTTPException(409, "Accounting journal is incomplete or unbalanced")
    manifest = {
        "entries": [(entry.id, entry.entry_date.isoformat(), entry.source, entry.source_ref) for entry in entries],
        "lines": [(line.id, line.entry_id, line.account_id, str(line.debit), str(line.credit), line.tag, line.tax_code)
                  for line in lines],
    }
    head = entries[-1].id
    return head, artifact_digest("cad_cash_close_journal", str(head), manifest)


def verify_journal_head(db, packet):
    if journal_snapshot(db) != (packet.journal_head, packet.ledger_snapshot_sha256):
        raise HTTPException(409, "The accounting journal changed after the signed cash close")


def reconcile_cash_position(packet, bank, blockers, *, live, preferences=None):
    if (bank["account_reference_sha256"], bank["bank_current_reported_minor"], bank["bank_available_reported_minor"],
            bank["basis"]) != (packet.account_reference_sha256, packet.bank_current_minor, packet.bank_available_minor,
                               "PLAID_BANK_BALANCE_OBSERVATION" if live else "PLAID_SANDBOX_BALANCE_OBSERVATION"):
        raise HTTPException(409, "Independent bank balance differs from the signed close")
    totals = dict.fromkeys(sorted(REQUIRED_PROTECTIONS), 0)
    reflected = 0
    for item in packet.protections:
        totals[item.category] += item.amount_minor
        if item.already_reflected_in_bank_available:
            reflected += item.amount_minor
    lower_balance = min(packet.bank_available_minor, packet.bank_current_minor)
    if reflected > packet.bank_current_minor - lower_balance:
        raise HTTPException(409, "Signed bank-held items cannot be reconciled to the reported available balance")
    protected = sum(totals.values()) - reflected
    cash = max(0, lower_balance - protected)
    eligible = min(cash, packet.retained_distributable_profit_minor)
    return {
        "scope": packet.scope.model_dump(), "currency": "CAD",
        "basis": "INDEPENDENT_CAD_CASH_CLOSE" if live else "SYNTHETIC_CAD_CASH_CLOSE",
        "bank_request_sha256": bank["request_reference_sha256"], "ledger_snapshot_sha256": packet.ledger_snapshot_sha256,
        "signed_close_sha256": cash_close_message(packet).decode(), "blockers": sorted(blockers),
        "protections_minor": totals, "protections_already_reflected_minor": reflected,
        "actual_accessible_funds_minor": cash if live and not blockers else None,
        "eligible_distributable_profit_minor": eligible if live and not blockers else None,
        "synthetic_cash_headroom_minor": cash if not live and not blockers else None,
        "synthetic_eligible_distribution_minor": eligible if not live and not blockers else None,
        "allocation": ({"basis": "OWNER_INPUT_RECOMMENDATION", **allocation_waterfall(eligible, preferences)}
                       if preferences is not None and not blockers else None),
        "requires_independent_distribution_review": True, "funds_movement_authorized": False,
    }
