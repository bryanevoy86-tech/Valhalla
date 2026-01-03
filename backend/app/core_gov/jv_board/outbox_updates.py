from __future__ import annotations
from typing import Any, Dict, List
from .service import board

def create_updates(to: str = "(paste)", channel: str = "email") -> Dict[str, Any]:
    b = board()
    items = b.get("items") or []
    lines = ["Valhalla — JV Update", ""]
    for x in items[:50]:
        lines.append(f"- {x.get('deal_id')} | {x.get('stage')} | {x.get('address')}")
    body = "\n".join(lines)

    try:
        from ..outbox import service as obx
        msg = obx.create(channel=channel, to=to, subject="JV Update", body=body, related={"type": "jv_update"})
        return {"outbox": msg, "count": len(items)}
    except Exception as e:
        return {"outbox": None, "count": len(items), "error": f"outbox unavailable: {type(e).__name__}: {e}"}
