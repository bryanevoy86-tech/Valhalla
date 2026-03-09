from __future__ import annotations
from typing import Any, Dict
from . import store as istore

def out_of(name: str, location: str = "", qty_to_set: float = 0.0) -> Dict[str, Any]:
    items = istore.list_items()
    it = next((x for x in items if x.get("status") == "active" and (x.get("name","").lower() == (name or "").lower()) and ((not location) or x.get("location")==location)), None)
    if it:
        it["qty"] = float(qty_to_set or 0.0)
        it["updated_at"] = istore._utcnow()  # type: ignore
        istore.save_items(items)
        
        # log usage event for forecast
        try:
            from backend.app.core_gov.forecast.service import log_usage  # type: ignore
            # assume we used 1 "unit" event when marked out_of (v1)
            log_usage(inv_id=it.get("id"), qty_used=max(0.0, float(it.get("target_qty") or 1.0)), notes="auto from out_of")
        except Exception:
            pass
        
        # also push to shopping (best-effort)
        try:
            from backend.app.core_gov.shopping import store as sstore  # type: ignore
            qty_need = float(it.get("target_qty") or 1.0)
            sstore.add(name=it.get("name"), qty=qty_need, unit=it.get("unit"), category=it.get("category"), est_unit_cost=float(it.get("est_unit_cost") or 0.0), source="inventory_low", ref_id=it.get("id"), notes="marked out_of")
        except Exception:
            pass
        return {"ok": True, "item": it}

    # if not in inventory, just add to shopping
    try:
        from backend.app.core_gov.shopping import store as sstore  # type: ignore
        rec = sstore.add(name=name, qty=1.0, unit="each", category="household", est_unit_cost=0.0, source="manual", ref_id="", notes="out_of (not in inventory)")
        return {"ok": True, "created_shopping": rec}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
