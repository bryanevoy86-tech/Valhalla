from __future__ import annotations
from typing import Any, Dict, List
from .service import list_events

def push_to_reminders(limit: int = 25) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    evs = list_events(limit=limit)

    try:
        from ..house_reminders import service as rsvc
        for e in evs:
            start = (e.get("start","") or "")
            due = start[:10] if len(start) >= 10 else ""
            if not due:
                continue
            rsvc.create(title=f"Event: {e.get('title','')}", due_date=due, kind="calendar", notes=e.get("location",""))
            created += 1
    except Exception as ex:
        warnings.append(f"reminders unavailable: {type(ex).__name__}: {ex}")

    return {"created": created, "warnings": warnings}
