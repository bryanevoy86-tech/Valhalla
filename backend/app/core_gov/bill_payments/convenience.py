from __future__ import annotations
from typing import Any, Dict

def upcoming(days: int = 14) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.budget_obligations.due import upcoming as up
        return up(days=days)
    except Exception:
        return {"items": [], "notes": ["upcoming unavailable"]}

def mark_paid_by_obligation(obligation_id: str, date: str, amount: float) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.bill_payments import service as psvc
        if hasattr(psvc, "mark_paid"):
            return psvc.mark_paid(obligation_id=obligation_id, date=date, amount=amount)
    except Exception as e:
        return {"error": f"bill_payments mark_paid unavailable: {type(e).__name__}: {e}"}
    return {"error": "bill_payments.mark_paid not found"}
