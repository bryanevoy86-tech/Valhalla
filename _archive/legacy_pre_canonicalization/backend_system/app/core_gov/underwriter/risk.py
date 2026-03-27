from __future__ import annotations
from typing import Any, Dict, List

def risk_summary(prop_id: str, jurisdiction: str = "CA-MB") -> Dict[str, Any]:
    warnings: List[str] = []
    # property
    try:
        from backend.app.core_gov.property.service import get as get_prop  # type: ignore
        p = get_prop(prop_id)
    except Exception:
        p = None
    if not p:
        return {"ok": False, "error": "property not found"}

    intel = p.get("intel") or {}
    neigh = int(intel.get("neighborhood_score") or 0)
    repairs = float(intel.get("repairs_total") or 0.0)

    # legal flags (best-effort by scanning a linked deal if any)
    legal_flags = []
    try:
        # find any deal attached by address match (v1)
        from backend.app.deals import store as dstore  # type: ignore
        deals = dstore.list_deals() if hasattr(dstore, "list_deals") else []
        match = next((d for d in deals if (d.get("address") or "") == (p.get("address") or "")), None)
        if match:
            from backend.app.core_gov.legal_filter.service import scan  # type: ignore
            legal_flags = (scan(deal=match, ruleset="v1").get("flags") or [])
    except Exception as e:
        warnings.append(f"legal scan unavailable: {type(e).__name__}")

    risk = 0
    if neigh and neigh < 40: risk += 15
    if repairs >= 30000: risk += 10
    if len(legal_flags) >= 1: risk += 10

    return {
        "ok": True,
        "prop_id": prop_id,
        "address": p.get("address"),
        "signals": {"neighborhood_score": neigh, "repairs_total": repairs, "legal_flags": legal_flags},
        "risk_v1": min(100, risk),
        "warnings": warnings
    }
