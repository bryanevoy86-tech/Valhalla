from __future__ import annotations

from typing import Any, Dict, List

def dashboard() -> Dict[str, Any]:
    warnings: List[str] = []

    try:
        from backend.app.core_gov.jv_links import service as jsvc  # type: ignore
        links = jsvc.list_links()
    except Exception as e:
        return {"warnings": [f"jv_links unavailable: {type(e).__name__}: {e}"], "by_partner": [], "by_deal": []}

    partners = {}
    try:
        from backend.app.core_gov.partners import service as psvc  # type: ignore
        for p in psvc.list_items():
            partners[p.get("id","")] = p
    except Exception as e:
        warnings.append(f"partners unavailable: {type(e).__name__}: {e}")

    by_partner = {}
    by_deal = {}

    for l in links:
        pid = l.get("partner_id","")
        did = l.get("deal_id","")
        by_partner.setdefault(pid, {"partner_id": pid, "partner_name": (partners.get(pid, {}) or {}).get("name",""), "links": 0, "split_total": 0.0})
        by_partner[pid]["links"] += 1
        by_partner[pid]["split_total"] += float(l.get("split_pct") or 0.0)

        by_deal.setdefault(did, {"deal_id": did, "links": 0, "split_total": 0.0})
        by_deal[did]["links"] += 1
        by_deal[did]["split_total"] += float(l.get("split_pct") or 0.0)

    out_partner = list(by_partner.values())
    out_partner.sort(key=lambda x: x.get("split_total",0.0), reverse=True)

    out_deal = list(by_deal.values())
    out_deal.sort(key=lambda x: x.get("split_total",0.0), reverse=True)

    return {"by_partner": out_partner[:500], "by_deal": out_deal[:500], "warnings": warnings}
