from __future__ import annotations
from typing import Any, Dict, List

def push_low_to_shopping() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []

    try:
        from backend.app.core_gov.house_inventory.service import list_low  # type: ignore
        low = list_low()
    except Exception as e:
        return {"created": 0, "warnings": [f"inventory unavailable: {type(e).__name__}"]}

    try:
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        existing = ssvc.list_items(status="open", limit=2000)
        existing_names = { (x.get("name") or "").strip().lower() for x in existing }
        for item in low:
            name = (item.get("name") or "").strip()
            if not name:
                continue
            if name.lower() in existing_names:
                continue
            ssvc.add(name=name, qty=float(item.get("reorder_qty") or 1.0), unit=item.get("unit") or "", priority="high", notes="auto from inventory low")
            created += 1
    except Exception as e:
        warnings.append(f"shopping unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
