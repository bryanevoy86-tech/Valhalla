from __future__ import annotations
from typing import Any, Dict, List

def create_from_open(limit: int = 25) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    items = []
    try:
        from backend.app.followups import store as fstore
        if hasattr(fstore, "list_followups"):
            items = fstore.list_followups(status="open")[:max(1, min(200, int(limit or 25)))]
    except Exception as e:
        warnings.append(f"followups unavailable: {type(e).__name__}: {e}")
        items = []

    try:
        from backend.app.core_gov.outbox import service as obx
        for fu in items:
            title = fu.get("title","")
            meta = fu.get("meta") or {}
            obx.create(channel="sms", to=meta.get("to","(paste number/email)"), subject="", body=title, related={"followup_id": fu.get("id")})
            created += 1
    except Exception as e:
        warnings.append(f"outbox create failed: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
