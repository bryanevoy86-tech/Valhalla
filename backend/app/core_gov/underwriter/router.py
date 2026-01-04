from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from .calc import calc_wholesale_mao, calc_brrrr_offer
from .deal_link import attach_property
from .deal_mao import write_mao
from .risk import risk_summary

router = APIRouter(prefix="/core/underwriter", tags=["core-underwriter"])

@router.get("/property/{prop_id}")
def underwrite_property(prop_id: str, mode: str = "wholesale", fee: float = 10000.0, arv_pct: float = 0.70, target_ltv: float = 0.75, closing_costs: float = 0.0, buffer: float = 0.0):
    try:
        from backend.app.core_gov.property.service import get as get_prop  # type: ignore
        p = get_prop(prop_id)
    except Exception:
        p = None
    if not p:
        raise HTTPException(status_code=404, detail="property not found")

    intel = p.get("intel") or {}
    arv = float(intel.get("arv") or 0.0)
    projected_rent = float(intel.get("projected_rent") or 0.0)
    repairs_total = float(intel.get("repairs_total") or 0.0)

    if mode == "brrrr":
        out = calc_brrrr_offer(arv=arv, repairs=repairs_total, target_ltv=target_ltv, closing_costs=closing_costs, buffer=buffer)
    else:
        out = calc_wholesale_mao(arv=arv, repairs=repairs_total, fee=fee, arv_pct=arv_pct)

    out["prop_id"] = prop_id
    out["address"] = p.get("address")
    out["intel_used"] = {"arv": arv, "repairs_total": repairs_total, "projected_rent": projected_rent}
    return out

@router.post("/deal/{deal_id}/attach_property")
def attach_property_ep(deal_id: str, prop_id: str):
    return attach_property(deal_id=deal_id, prop_id=prop_id)

@router.post("/deal/{deal_id}/write_mao")
def write_mao_ep(deal_id: str, mode: str = "wholesale", fee: float = 10000.0, arv_pct: float = 0.70, target_ltv: float = 0.75, closing_costs: float = 0.0, buffer: float = 0.0):
    return write_mao(deal_id=deal_id, mode=mode, fee=fee, arv_pct=arv_pct, target_ltv=target_ltv, closing_costs=closing_costs, buffer=buffer)

@router.get("/property/{prop_id}/risk")
def risk(prop_id: str, jurisdiction: str = "CA-MB"):
    return risk_summary(prop_id=prop_id, jurisdiction=jurisdiction)
