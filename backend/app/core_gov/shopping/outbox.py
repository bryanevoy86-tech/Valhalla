from __future__ import annotations
from typing import Any, Dict, List

def draft(to: str = "(paste)", channel: str = "sms") -> Dict[str, Any]:
    try:
        from .service import list_items
        items = list_items(status="open", limit=200)
    except Exception:
        items = []

    lines = ["Shopping List:"]
    for x in items:
        qty = x.get("qty")
        unit = x.get("unit") or ""
        lines.append(f"- {x.get('name')} ({qty}{(' '+unit) if unit else ''}) [{x.get('priority')}]")
    body = "\n".join(lines)

    try:
        from backend.app.core_gov.outbox import service as obx  # type: ignore
        msg = obx.create(channel=channel, to=to, subject="Shopping List", body=body, related={"type":"shopping_list"})
        return {"outbox": msg, "count": len(items)}
    except Exception as e:
        return {"outbox": None, "count": len(items), "error": f"outbox unavailable: {type(e).__name__}: {e}"}
