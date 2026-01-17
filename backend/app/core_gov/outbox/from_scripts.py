from __future__ import annotations
from typing import Any, Dict, List

def create_from_deal_script(deal_id: str, channel: str = "sms", to: str = "(paste)", tone: str = "neutral") -> Dict[str, Any]:
    warnings: List[str] = []
    body = ""
    try:
        from backend.app.deals.scripts_service import build_script
        body = build_script(deal_id=deal_id, channel=channel, tone=tone)
    except Exception as e:
        warnings.append(f"scripts unavailable: {type(e).__name__}: {e}")
        body = f"[SCRIPT PLACEHOLDER] Deal {deal_id}"

    try:
        from backend.app.core_gov.outbox import service as obx
        item = obx.create(channel=channel, to=to, subject="", body=body, related={"deal_id": deal_id, "tone": tone})
        return {"outbox": item, "warnings": warnings}
    except Exception as e:
        warnings.append(f"outbox create failed: {type(e).__name__}: {e}")
        return {"outbox": None, "warnings": warnings}
