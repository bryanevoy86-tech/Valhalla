from __future__ import annotations
from typing import Any, Dict, List
from . import store

def push(days_ahead: int = 7) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    # v1 uses renewal_day only (not calendar-aware by month length)
    items = [x for x in store.list_items() if x.get("status") == "active"]
    try:
        from datetime import date
        today = date.today()
        day = today.day
        upcoming = [s for s in items if abs(int(s.get("renewal_day") or 1) - day) <= max(1, int(days_ahead or 7))]
    except Exception:
        upcoming = items[:10]

    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        for s in upcoming[:50]:
            rsvc.create(
                title=f"Subscription renewal: {s.get('name')}",
                due_date="",
                kind="subscription",
                notes=f"amount={s.get('amount')} {s.get('currency')} cadence={s.get('cadence')} day={s.get('renewal_day')}",
            )
            created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings, "upcoming": len(upcoming)}
