from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List
from . import store

def _next_due_monthly(due_day: int) -> str:
    today = date.today()
    dday = max(1, min(28, int(due_day or 1)))  # safe day
    due = date(today.year, today.month, dday)
    if due < today:
        # next month
        ny = today.year + (1 if today.month == 12 else 0)
        nm = 1 if today.month == 12 else today.month + 1
        due = date(ny, nm, dday)
    return due.isoformat()

def _next_due_every_n_months(due_day: int, n: int) -> str:
    today = date.today()
    dday = max(1, min(28, int(due_day or 1)))
    n = max(1, min(24, int(n or 1)))
    # brute: scan next 24 months for due date on cadence
    # v1 assumes due month is current month modulo n (simple enough for tracking)
    for i in range(0, 24):
        y = today.year + ((today.month - 1 + i) // 12)
        m = ((today.month - 1 + i) % 12) + 1
        if i % n != 0:
            continue
        due = date(y, m, dday)
        if due >= today:
            return due.isoformat()
    return date(today.year, today.month, dday).isoformat()

def upcoming(limit: int = 50) -> Dict[str, Any]:
    bills = [b for b in store.list_bills() if b.get("status") == "active"]
    rows: List[Dict[str, Any]] = []
    for b in bills:
        cad = (b.get("cadence") or "monthly").lower()
        if cad == "every_n_months":
            due = _next_due_every_n_months(b.get("due_day") or 1, b.get("due_months") or 1)
        else:
            due = _next_due_monthly(b.get("due_day") or 1)
        rows.append({**b, "next_due": due})
    rows.sort(key=lambda x: x.get("next_due",""))
    return {"upcoming": rows[:max(1, min(2000, int(limit or 50)))]}
