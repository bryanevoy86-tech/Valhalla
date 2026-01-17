from __future__ import annotations
from typing import Any, Dict

def push_replace_to_shopping(threshold: float = 200.0) -> Dict[str, Any]:
    created = 0
    try:
        from backend.app.core_gov.assets.replace import list_items  # type: ignore
        repl = [x for x in list_items() if x.get("status") == "open"]
    except Exception:
        repl = []

    try:
        from backend.app.core_gov.shopping import store as sstore  # type: ignore
    except Exception:
        return {"created": 0, "error": "shopping unavailable"}

    for r in repl[:200]:
        title = r.get("title") or ""
        est = float(r.get("est_cost") or 0.0)
        sstore.add(name=title, qty=1.0, unit="each", category="household", est_unit_cost=est, source="schedule", ref_id=r.get("id") or "", notes="from replace tracker")
        created += 1
        if est >= float(threshold or 0.0):
            try:
                from backend.app.core_gov.approvals import store as astore  # type: ignore
                astore.create(kind="purchase", title=f"Approve replacement: {title}", amount=est, currency="CAD", meta={"replace_id": r.get("id")})
            except Exception:
                pass

    return {"created": created}
