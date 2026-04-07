from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.finance.deal_ledger import DealLedger
from app.finance.disbursement_engine import build_disbursement_plan
from app.finance.finance_control_service import queue_financial_intent_for_approval


@dataclass
class FinancialPackageResult:
    package_id: str
    deal_id: str
    triggered: bool
    ledger: dict[str, Any] | None
    disbursement_count: int
    queued_count: int
    blocked_count: int
    intents: list[dict[str, Any]]
    reason: str | None = None


def build_financial_package(deal: dict[str, Any]) -> FinancialPackageResult:
    deal_id = str(deal.get("deal_id", "unknown"))
    requested_by = str(deal.get("requested_by", "heimdall"))
    package_id = f"{deal_id}__finance_package"

    if deal_id == "unknown":
        return FinancialPackageResult(
            package_id=package_id,
            deal_id=deal_id,
            triggered=False,
            ledger=None,
            disbursement_count=0,
            queued_count=0,
            blocked_count=0,
            intents=[],
            reason="deal_id is required",
        )

    ledger = DealLedger(
        deal_id=deal_id,
        purchase_price=float(deal.get("purchase_price", 0) or 0),
        assignment_fee=float(deal.get("assignment_fee", 0) or 0),
        earnest_money=float(deal.get("earnest_money", 0) or 0),
        closing_costs=float(deal.get("closing_costs", 0) or 0),
        revenue=float(deal.get("revenue", 0) or 0),
        expenses=float(deal.get("expenses", 0) or 0),
    )
    ledger.calculate_expected_profit()
    ledger.calculate_actual_profit()

    plan = build_disbursement_plan(deal_id, deal)

    queued_results: list[dict[str, Any]] = []
    blocked_count = 0
    queued_count = 0

    for idx, intent in enumerate(plan, start=1):
        intent_id = f"{deal_id}__intent_{idx}__{intent.purpose}"
        result = queue_financial_intent_for_approval(
            deal_id=deal_id,
            intent_id=intent_id,
            amount=float(intent.amount),
            purpose=str(intent.purpose),
            payee=str(intent.payee),
            requested_by=requested_by,
        )
        result["payer"] = intent.payer
        result["payee"] = intent.payee
        result["amount"] = intent.amount
        result["purpose"] = intent.purpose
        queued_results.append(result)

        if result.get("blocked"):
            blocked_count += 1
        if result.get("queued"):
            queued_count += 1

    return FinancialPackageResult(
        package_id=package_id,
        deal_id=deal_id,
        triggered=True,
        ledger=ledger.to_dict(),
        disbursement_count=len(plan),
        queued_count=queued_count,
        blocked_count=blocked_count,
        intents=queued_results,
        reason=None,
    )
