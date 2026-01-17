from __future__ import annotations
from typing import Any, Dict, List
from . import store

def push_reminders() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    d = store.get()
    items = d.get("items") or {}
    missing = [k for k, v in items.items() if not v]

    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        for k in missing[:50]:
            rsvc.create(title=f"Trust/Entity task: {k}", due_date="", kind="trust", notes="auto from trust_status")
            created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "missing": missing[:200], "warnings": warnings}
