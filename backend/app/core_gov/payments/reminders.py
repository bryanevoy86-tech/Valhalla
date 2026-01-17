from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List
from . import store
from .service import compute_next

def push(days_ahead: int = 5) -> Dict[str, Any]:
    days_ahead = max(1, min(30, int(days_ahead or 5)))
    today = date.today()
    cutoff = (today + timedelta(days=days_ahead)).isoformat()

    items = [x for x in store.list_items() if x.get("status") == "active"]
    due = []
    for p in items:
        nd = compute_next(p, from_date=today.isoformat())
        if nd and today.isoformat() <= nd <= cutoff:
            due.append((nd, p))

    created = 0
    warnings: List[str] = []
    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        for nd, p in due[:100]:
            rsvc.create(
                title=f"Due soon: {p.get('name')} ({p.get('amount')} {p.get('currency')})",
                due_date=nd,
                kind="payment_due",
                notes=f"payment_id={p.get('id')} autopay={p.get('autopay_enabled')} verified={p.get('autopay_verified')}",
            )
            created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings, "due_count": len(due)}
