from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List
from backend.app.core_gov.shopping import service as sservice  # type: ignore
from backend.app.core_gov.schedule import store as scstore  # type: ignore

def generate(within_days: int = 30, limit: int = 50) -> Dict[str, Any]:
    within_days = max(1, min(365, int(within_days or 30)))
    cutoff = (date.today() + timedelta(days=within_days)).isoformat()

    events = scstore.list_all()
    needs = [e for e in events if (e.get("kind") == "need") and (e.get("status") == "scheduled") and (e.get("date") or "") <= cutoff]

    existing = sservice.list_items()
    open_names = {x.get("name","").lower() for x in existing if x.get("status") == "open"}

    created = 0
    for e in needs[:max(1, min(2000, int(limit or 50)))]:
        title = (e.get("title") or "").replace("Need:", "").strip()
        if not title:
            continue
        if title.lower() in open_names:
            continue
        try:
            sservice.create_item({
                "name": title,
                "qty": 1.0,
                "unit": "each",
                "category": "household",
                "est_unit_cost": 0.0,
                "source": "schedule",
                "tags": ["from_schedule_need"],
            })
            created += 1
        except Exception:
            pass

    return {"created": created, "scanned": len(needs)}
