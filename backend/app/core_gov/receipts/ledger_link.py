from __future__ import annotations
from typing import Any, Dict

def post_to_ledger(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort: if ledger exists, create an expense entry.
    """
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
    except Exception as e:
        return {"ok": False, "error": "ledger not available"}

    try:
        # adapt if your ledger service differs; v1 tries a common create() pattern
        if hasattr(lsvc, "create"):
            tx = lsvc.create({
                "type": "expense",
                "amount": float(receipt.get("amount") or 0.0),
                "currency": receipt.get("currency") or "CAD",
                "date": receipt.get("date"),
                "category": receipt.get("category") or "household",
                "memo": f"Receipt: {receipt.get('vendor')}",
                "meta": {"receipt_id": receipt.get("id")}
            })
            return {"ok": True, "tx": tx}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    return {"ok": False, "error": "ledger create() not found"}
