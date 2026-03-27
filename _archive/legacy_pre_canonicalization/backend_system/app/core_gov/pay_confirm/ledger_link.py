from __future__ import annotations
from typing import Any, Dict

def post_confirmation_to_ledger(conf: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
    except Exception:
        return {"ok": False, "error": "ledger not available"}

    try:
        if hasattr(lsvc, "create"):
            tx = lsvc.create({
                "type": "expense",
                "amount": float(conf.get("amount") or 0.0),
                "currency": conf.get("currency") or "CAD",
                "date": conf.get("paid_on"),
                "category": "bills",
                "memo": f"Payment confirmation {conf.get('payment_id')}",
                "meta": {"pay_confirm_id": conf.get("id"), "payment_id": conf.get("payment_id")}
            })
            return {"ok": True, "tx": tx}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    return {"ok": False, "error": "ledger create() not found"}
