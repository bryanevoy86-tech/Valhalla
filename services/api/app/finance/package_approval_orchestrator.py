from __future__ import annotations

from typing import Any

from app.finance.disbursement_engine import build_disbursement_plan
from app.finance.finance_control_service import approve_financial_intent


def approve_financial_package(deal_id: str, deal_data: dict[str, Any], approver: str) -> dict[str, Any]:
    plan = build_disbursement_plan(deal_id, deal_data)

    if not plan:
        return {
            "package_approved": False,
            "deal_id": deal_id,
            "reason": "No disbursement intents found for deal",
            "results": [],
        }

    results = []
    approved_count = 0
    failed_count = 0

    for idx, intent in enumerate(plan, start=1):
        intent_id = f"{deal_id}__intent_{idx}__{intent.purpose}"
        try:
            result = approve_financial_intent(intent_id, approver)
            results.append(result)
            if result.get("approved"):
                approved_count += 1
        except Exception as exc:
            failed_count += 1
            results.append(
                {
                    "intent_id": intent_id,
                    "approved": False,
                    "error": str(exc),
                }
            )

    return {
        "package_approved": failed_count == 0,
        "deal_id": deal_id,
        "approved_count": approved_count,
        "failed_count": failed_count,
        "total_count": len(plan),
        "results": results,
    }
