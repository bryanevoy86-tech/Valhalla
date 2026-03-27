from __future__ import annotations
from typing import Any, Dict, List
from .due import upcoming

def create_due_followups(days: int = 7) -> Dict[str, Any]:
    due = upcoming(days=days).get("items", [])
    created = 0
    warnings: List[str] = []
    try:
        from backend.app.followups import store as fstore  # type: ignore
        for x in due:
            ob = x.get("obligation") or {}
            fstore.create_followup({
                "type": "bill",
                "title": f"Pay: {ob.get('name','(bill)')}",
                "due_date": x.get("due_date",""),
                "status": "open",
                "meta": {"obligation_id": ob.get("id"), "amount": x.get("amount"), "autopay": ob.get("autopay", False)},
            })
            created += 1
    except Exception as e:
        warnings.append(f"followups unavailable (safe): {type(e).__name__}: {e}")
    return {"created": created, "warnings": warnings}
