from __future__ import annotations
from datetime import date
from typing import Any, Dict, List
from . import store

def push() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    dow = ["mon","tue","wed","thu","fri","sat","sun"][date.today().weekday()]
    routines = [r for r in store.list_items() if r.get("status") == "active" and r.get("freq") == "weekly" and r.get("day_of_week") == dow]

    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        for r in routines[:50]:
            rsvc.create(
                title=f"Routine today: {r.get('title')}",
                due_date="",
                kind="routine",
                notes=f"items={len(r.get('items') or [])} routine_id={r.get('id')}",
            )
            created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings, "routines": len(routines)}
