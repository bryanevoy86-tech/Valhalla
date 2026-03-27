from __future__ import annotations
from typing import Any, Dict, List
from .service import plan

def create_income_followups(days: int = 14) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    p = plan(days=days)
    expected = p.get("expected") or []

    try:
        from ..followups import service as fsvc
        for e in expected:
            fsvc.create(
                task_type="income",
                title=f"Confirm income: {e.get('name','')}",
                due_date=e.get("date",""),
                details={"income_id": e.get("income_id"), "amount": e.get("amount"), "currency": e.get("currency")},
            )
            created += 1
    except Exception as ex:
        warnings.append(f"followups unavailable: {type(ex).__name__}: {ex}")

    return {"created": created, "warnings": warnings}
