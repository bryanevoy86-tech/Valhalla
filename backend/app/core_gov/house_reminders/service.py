from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

def create_followups(days_ahead: int = 7) -> Dict[str, Any]:
    warnings: List[str] = []
    created = 0
    today = date.today()
    end = today + timedelta(days=max(1, int(days_ahead or 7)))

    try:
        from backend.app.core_gov.house_calendar import service as csvc  # type: ignore
        events = csvc.list_items(date_from=today.isoformat(), date_to=end.isoformat())
    except Exception as e:
        return {"created": 0, "warnings": [f"house_calendar unavailable: {type(e).__name__}: {e}"]}

    try:
        from backend.app.followups import store as fstore  # type: ignore
        for ev in events:
            try:
                fstore.create_followup({
                    "type": "event",
                    "event_id": ev.get("id",""),
                    "title": f"Upcoming: {ev.get('title','')}",
                    "due_date": ev.get("date",""),
                    "status": "open",
                    "meta": {"time": ev.get("time",""), "location": ev.get("location",""), "category": ev.get("category","")},
                })
                created += 1
            except Exception:
                warnings.append("followups: create_followup missing/failed (safe)")
                break
    except Exception as e:
        warnings.append(f"followups unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
