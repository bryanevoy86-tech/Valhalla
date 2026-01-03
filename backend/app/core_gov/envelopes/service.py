from __future__ import annotations
from typing import Any, Dict

def month_totals(month: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"month": month, "by_category": {}, "notes": []}
    try:
        from ..ledger_light import service as lsvc
        rows = lsvc.list_items(month=month) if hasattr(lsvc, "list_items") else []
    except Exception as e:
        rows = []
        out["notes"].append(f"ledger unavailable: {type(e).__name__}")

    for r in rows or []:
        if (r.get("kind") or "") != "expense":
            continue
        cat = (r.get("category") or "misc").strip().lower()
        out["by_category"][cat] = round(float(out["by_category"].get(cat, 0.0)) + float(r.get("amount") or 0.0), 2)
    return out
