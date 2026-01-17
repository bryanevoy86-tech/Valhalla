from __future__ import annotations
from typing import Any, Dict, List
from . import service as ssvc

def to_followups(status: str = "open") -> Dict[str, Any]:
    items = ssvc.list_items(status=status)
    created = 0
    warnings: List[str] = []
    try:
        from backend.app.followups import store as fstore  # type: ignore
        for it in items:
            fstore.create_followup({
                "type": "shopping",
                "title": f"Buy: {it.get('item','')}",
                "due_date": "",
                "status": "open",
                "meta": {"shopping_id": it.get("id"), "priority": it.get("priority"), "qty": it.get("qty")},
            })
            created += 1
    except Exception as e:
        warnings.append(f"followups unavailable (safe): {type(e).__name__}: {e}")
    return {"created": created, "warnings": warnings}
