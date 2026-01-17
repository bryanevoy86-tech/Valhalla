from __future__ import annotations
from typing import Any, Dict

def attach_property(deal_id: str, prop_id: str) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.property.service import get as get_prop  # type: ignore
        p = get_prop(prop_id)
    except Exception:
        p = None
    if not p:
        return {"ok": False, "error": "property not found"}

    try:
        from backend.app.deals import store as dstore  # type: ignore
        deal = dstore.get_deal(deal_id)
    except Exception:
        deal = None
    if not deal:
        return {"ok": False, "error": "deal not found"}

    meta = deal.get("meta") or {}
    meta["property_id"] = prop_id
    meta["property_address"] = p.get("address")
    deal["meta"] = meta

    # best-effort persist
    try:
        if hasattr(dstore, "save_deal"):
            dstore.save_deal(deal)
        elif hasattr(dstore, "patch_deal"):
            dstore.patch_deal(deal_id, {"meta": meta})
    except Exception:
        pass

    return {"ok": True, "deal_id": deal_id, "property_id": prop_id}
