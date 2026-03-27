from __future__ import annotations
from typing import Any, Dict, List
from .tradelines import list_items as list_tradelines

def push_followups() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    items = list_tradelines()

    try:
        from backend.app.followups import store as fstore  # type: ignore
        for t in items:
            if t.get("status") != "todo":
                continue
            fstore.create_followup({
                "type": "credit",
                "title": f"Credit task: open {t.get('vendor')}",
                "due_date": "",
                "status": "open",
                "meta": {"tradeline_id": t.get("id"), "tier": t.get("tier")},
            })
            created += 1
    except Exception as e:
        warnings.append(f"followups unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
