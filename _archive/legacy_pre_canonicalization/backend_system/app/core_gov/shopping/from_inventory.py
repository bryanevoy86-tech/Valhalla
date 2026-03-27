from __future__ import annotations
from typing import Any, Dict, List
from backend.app.core_gov.shopping import store as sstore  # type: ignore
from backend.app.core_gov.inventory.reorder import low_stock  # type: ignore

def generate(limit: int = 50) -> Dict[str, Any]:
    low = low_stock(limit=500).get("items") or []
    created = 0
    existing = sstore.list_items()
    open_keys = {(x.get("name","").lower(), x.get("status")) for x in existing}

    for it in low[:max(1, min(2000, int(limit or 50)))]:
        name = it.get("name","")
        if (name.lower(), "open") in open_keys:
            continue
        # qty needed = target - qty (fallback 1)
        qty = float(it.get("target_qty") or 0.0) - float(it.get("qty") or 0.0)
        qty = qty if qty > 0 else 1.0
        sstore.add(
            name=name,
            qty=qty,
            unit=it.get("unit") or "each",
            category=it.get("category") or "household",
            est_unit_cost=float(it.get("est_unit_cost") or 0.0),
            source="inventory_low",
            ref_id=it.get("id") or "",
            notes=f"low_stock: {it.get('location','')}"
        )
        created += 1

    return {"created": created}
