from __future__ import annotations
from typing import Any, Dict
from . import service as sservice

def request_approvals(threshold: float = 200.0) -> Dict[str, Any]:
    threshold = float(threshold or 0.0)
    items = sservice.list_items(status="open")
    created = 0
    try:
        from backend.app.core_gov.approvals import service as aservice  # type: ignore
    except Exception:
        return {"created": 0, "error": "approvals module not available"}

    for it in items[:500]:
        est = float(it.get("est_unit_cost") or 0.0) * float(it.get("qty") or 0.0)
        if est >= threshold:
            try:
                aservice.create(
                    title=f"Approve purchase: {it.get('name')}",
                    action="approve_purchase",
                    payload={"shopping_id": it.get("id"), "amount": est}
                )
                created += 1
            except Exception:
                pass
    return {"created": created}
