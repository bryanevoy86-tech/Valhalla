from __future__ import annotations
from typing import Any, Dict
from .calc import calc_wholesale_mao, calc_brrrr_offer

def _get_deal(deal_id: str):
    try:
        from backend.app.deals import store as dstore  # type: ignore
        return dstore, dstore.get_deal(deal_id)
    except Exception:
        return None, None

def _get_prop(prop_id: str):
    try:
        from backend.app.core_gov.property.service import get as get_prop  # type: ignore
        return get_prop(prop_id)
    except Exception:
        return None

def write_mao(deal_id: str, mode: str = "wholesale", fee: float = 10000.0, arv_pct: float = 0.70, target_ltv: float = 0.75, closing_costs: float = 0.0, buffer: float = 0.0) -> Dict[str, Any]:
    dstore, deal = _get_deal(deal_id)
    if not deal:
        return {"ok": False, "error": "deal not found"}

    prop_id = ((deal.get("meta") or {}).get("property_id") or "").strip()
    if not prop_id:
        return {"ok": False, "error": "deal has no attached property_id"}

    p = _get_prop(prop_id)
    if not p:
        return {"ok": False, "error": "attached property not found"}

    intel = p.get("intel") or {}
    arv = float(intel.get("arv") or 0.0)
    repairs_total = float(intel.get("repairs_total") or 0.0)

    if mode == "brrrr":
        calc = calc_brrrr_offer(arv=arv, repairs=repairs_total, target_ltv=target_ltv, closing_costs=closing_costs, buffer=buffer)
        mao = float(calc.get("max_offer") or 0.0)
    else:
        calc = calc_wholesale_mao(arv=arv, repairs=repairs_total, fee=fee, arv_pct=arv_pct)
        mao = float(calc.get("mao") or 0.0)

    meta = deal.get("meta") or {}
    meta["underwrite_v1"] = {"mode": mode, "calc": calc, "mao": mao}
    deal["meta"] = meta

    # best-effort persist
    try:
        if hasattr(dstore, "save_deal"):
            dstore.save_deal(deal)
        elif hasattr(dstore, "patch_deal"):
            dstore.patch_deal(deal_id, {"meta": meta})
    except Exception:
        pass

    return {"ok": True, "deal_id": deal_id, "property_id": prop_id, "mao": mao, "calc": calc}
