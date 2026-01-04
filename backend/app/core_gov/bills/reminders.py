from __future__ import annotations
from typing import Any, Dict, List
from .due import upcoming

def push(days_ahead: int = 7) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    try:
        up = upcoming(limit=500).get("upcoming") or []
    except Exception:
        up = []
    try:
        from datetime import date
        today = date.today().isoformat()
    except Exception:
        today = ""

    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        for b in up:
            # simple: always create reminder for next_due within days_ahead (date compare as strings works ISO)
            due = (b.get("next_due") or "")
            if not due:
                continue
            # cheap comparison: if due <= today+days_ahead, push
            from datetime import date, timedelta
            cutoff = (date.today() + timedelta(days=max(0, int(days_ahead or 7)))).isoformat()
            if due <= cutoff:
                rsvc.create(
                    title=f"Bill due: {b.get('name')} (${b.get('amount')})",
                    due_date=due,
                    kind="bill",
                    notes=f"payee={b.get('payee','')} autopay={b.get('autopay')}",
                )
                created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
