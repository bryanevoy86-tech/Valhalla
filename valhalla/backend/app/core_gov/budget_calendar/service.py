from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

def _parse_date(s: str) -> date:
    if not s:
        return date.today()
    return datetime.strptime(s, "%Y-%m-%d").date()

def _next_month(d: date, months: int) -> date:
    y = d.year
    m = d.month + months
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    return date(y, m, min(d.day, 28))

def project(days_ahead: int = 45, from_date: str = "") -> Dict[str, Any]:
    warnings: List[str] = []
    start = _parse_date(from_date) if from_date else date.today()
    end = start + timedelta(days=max(7, int(days_ahead or 45)))

    try:
        from backend.app.core_gov.budget_obligations import service as obsvc  # type: ignore
        obs = obsvc.list_items(status="active")
    except Exception as e:
        return {"items": [], "warnings": [f"budget_obligations unavailable: {type(e).__name__}: {e}"]}

    items = []
    for o in obs:
        cadence = o.get("cadence")
        due_day = int(o.get("due_day") or 1)
        due_months = int(o.get("due_months") or 1)
        amt = float(o.get("amount") or 0.0)

        anchor = start
        if cadence in ("monthly","quarterly","yearly","custom_months"):
            anchor = date(start.year, start.month, min(max(1, due_day), 28))
            if anchor < start:
                anchor = _next_month(anchor, due_months if cadence != "monthly" else 1)
        elif cadence == "weekly":
            target = due_day
            delta = (target - anchor.weekday()) % 7
            anchor = anchor + timedelta(days=delta)

        cur = anchor
        while cur <= end:
            if cur >= start:
                items.append({
                    "date": cur.isoformat(),
                    "obligation_id": o.get("id",""),
                    "name": o.get("name",""),
                    "amount": amt,
                    "pay_to": o.get("pay_to",""),
                    "category": o.get("category",""),
                    "autopay_status": o.get("autopay_status","unknown"),
                })
            if cadence == "weekly":
                cur = cur + timedelta(days=7)
            elif cadence == "monthly":
                cur = _next_month(cur, 1)
            else:
                cur = _next_month(cur, due_months)

    items.sort(key=lambda x: x["date"])
    return {"from": start.isoformat(), "to": end.isoformat(), "items": items, "warnings": warnings}

def create_followups_for_window(days_ahead: int = 14) -> Dict[str, Any]:
    cal = project(days_ahead=days_ahead)
    warnings = cal.get("warnings") or []
    created = 0
    try:
        from backend.app.followups import store as fstore  # type: ignore
        for it in cal.get("items") or []:
            try:
                fstore.create_followup({
                    "type": "bill_due",
                    "obligation_id": it.get("obligation_id",""),
                    "title": f"Pay: {it.get('name','')}",
                    "due_date": it.get("date",""),
                    "status": "open",
                    "amount": it.get("amount", 0.0),
                    "pay_to": it.get("pay_to",""),
                })
                created += 1
            except Exception:
                warnings.append("followups: create_followup missing/failed (safe)")
                break
    except Exception as e:
        warnings.append(f"followups unavailable: {type(e).__name__}: {e}")
    return {"days_ahead": int(days_ahead or 14), "created": created, "warnings": warnings}
