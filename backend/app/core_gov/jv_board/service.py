from __future__ import annotations
from typing import Any, Dict, List

def board() -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    notes: List[str] = []

    try:
        from ..deals import service as dsvc
        deals = dsvc.list_deals() if hasattr(dsvc, "list_deals") else []
    except Exception as e:
        deals = []
        notes.append(f"deals unavailable: {type(e).__name__}")

    for d in deals or []:
        meta = d.get("meta") or {}
        if not meta.get("jv_partner_id") and not meta.get("jv"):
            continue
        rows.append({
            "deal_id": d.get("id"),
            "address": d.get("address",""),
            "stage": d.get("stage",""),
            "status": d.get("status",""),
            "jv_partner_id": meta.get("jv_partner_id",""),
            "summary": (d.get("summary") or "")[:240],
        })

    rows.sort(key=lambda x: x.get("stage",""))
    return {"count": len(rows), "items": rows[:2000], "notes": notes}
