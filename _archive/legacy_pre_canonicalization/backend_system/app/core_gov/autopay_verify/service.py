from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

def verify(days_back: int = 7, days_ahead: int = 7) -> Dict[str, Any]:
    warnings: List[str] = []
    flagged: List[Dict[str, Any]] = []

    try:
        from backend.app.core_gov.budget_calendar import service as calsvc  # type: ignore
        cal = calsvc.project(days_ahead=int(days_ahead or 7))
        due = cal.get("items") or []
    except Exception as e:
        return {"flagged": [], "warnings": [f"budget_calendar unavailable: {type(e).__name__}: {e}"]}

    payments = []
    try:
        from backend.app.core_gov.bill_payments import service as psvc  # type: ignore
        payments = psvc.list_items()
    except Exception as e:
        warnings.append(f"bill_payments unavailable: {type(e).__name__}: {e}")

    paid_dates_by_obl = {}
    for p in payments:
        paid_dates_by_obl.setdefault(p.get("obligation_id",""), set()).add(p.get("paid_date",""))

    for d in due:
        if d.get("autopay_status") != "on":
            continue
        oid = d.get("obligation_id","")
        dt = d.get("date","")
        # if no payment on exact due date, flag
        if dt not in paid_dates_by_obl.get(oid, set()):
            flagged.append({
                "obligation_id": oid,
                "name": d.get("name",""),
                "due_date": dt,
                "amount": d.get("amount", 0.0),
                "hint": "Autopay ON but no payment logged — verify bank/app receipt.",
            })

    flagged.sort(key=lambda x: x.get("due_date",""))
    return {"flagged": flagged[:500], "warnings": warnings}
