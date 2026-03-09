from __future__ import annotations
from typing import Any, Dict

def build(deal_id: str, kind: str = "sms", tone: str = "neutral") -> Dict[str, Any]:
    try:
        from backend.app.deals import store as dstore  # type: ignore
        deal = dstore.get_deal(deal_id)
    except Exception:
        deal = None
    if not deal:
        return {"ok": False, "error": "deal not found"}

    # best-effort script builder (if installed)
    body = ""
    try:
        from backend.app.deals.scripts_service import build_script  # type: ignore
        body = build_script(deal=deal, channel=kind, tone=tone)
    except Exception:
        body = f"{deal.get('address','(deal)')} — checking in. Are you free to talk today?"

    return {"ok": True, "deal_id": deal_id, "kind": kind, "tone": tone, "body": body}
