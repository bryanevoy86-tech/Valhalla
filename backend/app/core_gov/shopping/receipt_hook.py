from __future__ import annotations
from typing import Any, Dict

def on_bought(shopping_item: Dict[str, Any], vendor: str = "", date: str = "") -> Dict[str, Any]:
    # best-effort: if receipts module exists, create a placeholder receipt
    try:
        from backend.app.core_gov.receipts import service as rservice  # type: ignore
        amount = float(shopping_item.get("est_unit_cost") or 0.0) * float(shopping_item.get("qty") or 0.0)
        if amount <= 0:
            return {"ok": False, "skipped": True, "reason": "no cost estimate"}
        return {
            "ok": True,
            "receipt": rservice.create({
                "vendor": vendor or "UNKNOWN",
                "total": amount,
                "date": date or "",
                "currency": "CAD",
                "source": "shopping_item",
            })
        }
    except Exception as e:
        return {"ok": False, "error": f"receipts unavailable: {type(e).__name__}"}
