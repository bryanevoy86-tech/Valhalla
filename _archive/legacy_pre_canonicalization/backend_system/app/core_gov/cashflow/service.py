from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List

def forecast(days: int = 30) -> Dict[str, Any]:
    days = max(7, min(180, int(days or 30)))
    start = date.today()
    end = start + timedelta(days=days)

    bills = []
    subs = []
    warnings: List[str] = []

    # Bills (expects bills.store with list_bills())
    try:
        from backend.app.core_gov.bills import store as bstore  # type: ignore
        if hasattr(bstore, "list_bills"):
            bills = [x for x in bstore.list_bills() if x.get("status") in (None, "active")]
    except Exception:
        warnings.append("bills unavailable")

    # Subs
    try:
        from backend.app.core_gov.subscriptions import store as sstore  # type: ignore
        subs = [x for x in sstore.list_items() if x.get("status") == "active"]
    except Exception:
        warnings.append("subscriptions unavailable")

    rows = []
    for b in bills:
        dd = int(b.get("due_day") or 1)
        amt = float(b.get("amount") or 0.0)
        rows.append({"type":"bill", "name": b.get("name"), "amount": amt, "currency": b.get("currency","CAD"), "day_of_month": dd})

    for s in subs:
        dd = int(s.get("renewal_day") or 1)
        amt = float(s.get("amount") or 0.0)
        rows.append({"type":"subscription", "name": s.get("name"), "amount": amt, "currency": s.get("currency","CAD"), "day_of_month": dd})

    # Expand into specific dates for next N days
    schedule = []
    for i in range(days + 1):
        d = start + timedelta(days=i)
        dom = d.day
        for r in rows:
            if int(r.get("day_of_month") or 0) == dom:
                schedule.append({"date": d.isoformat(), **r})

    schedule.sort(key=lambda x: x.get("date",""))
    total = sum(float(x.get("amount") or 0.0) for x in schedule)
    
    # Also include payments schedule if available
    try:
        from backend.app.core_gov.payments import store as pstore  # type: ignore
        from backend.app.core_gov.payments.service import schedule as psched  # type: ignore
        fc_payments = psched(pstore.list_items(), days=days)
    except Exception:
        fc_payments = []
    
    return {"days": days, "items": schedule, "estimated_total": round(total, 2), "warnings": warnings, "payments": fc_payments}
