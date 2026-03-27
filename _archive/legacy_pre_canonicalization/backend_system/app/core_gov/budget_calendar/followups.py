from __future__ import annotations

from typing import Any, Dict, List
from . import service as cal

def create_followups(days_ahead: int = 14) -> Dict[str, Any]:
    warnings: List[str] = []
    created = 0
    cal_res = cal.project(days_ahead=days_ahead)
    items = cal_res.get("items") or []
    warnings.extend(cal_res.get("warnings") or [])

    try:
        from backend.app.followups import store as fstore  # type: ignore
    except Exception as e:
        return {"created": 0, "warnings": warnings + [f"followups unavailable: {type(e).__name__}: {e}"]}

    for it in items:
        try:
            fstore.create_followup({
                "type": "bill",
                "obligation_id": it.get("obligation_id",""),
                "title": f"Pay: {it.get('name','')}",
                "due_date": it.get("date",""),
                "status": "open",
                "meta": {"amount": it.get("amount",0.0), "autopay_status": it.get("autopay_status","unknown")},
            })
            created += 1
        except Exception as e:
            warnings.append(f"followup create failed: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
