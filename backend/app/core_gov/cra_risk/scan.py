from __future__ import annotations
from typing import Any, Dict, List

def scan(month: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"month": month, "hits": [], "notes": []}

    try:
        from . import store as rstore
        cfg = rstore.get()
        risk_map = cfg.get("category_risk") or {}
    except Exception:
        risk_map = {}

    try:
        from ..ledger_light import service as lsvc
        rows = lsvc.list_items(month=month) if hasattr(lsvc, "list_items") else []
    except Exception as e:
        out["notes"].append(f"ledger unavailable: {type(e).__name__}")
        rows = []

    for r in rows or []:
        if (r.get("kind") or "") != "expense":
            continue
        cat = (r.get("category") or "").strip().lower()
        level = (risk_map.get(cat) or "")
        if level in ("aggressive", "medium"):
            out["hits"].append({
                "id": r.get("id"),
                "category": cat,
                "risk": level,
                "amount": float(r.get("amount") or 0.0),
                "description": r.get("description",""),
            })

    out["hits"].sort(key=lambda x: (x["risk"], -x["amount"]))
    return out
