from __future__ import annotations
from typing import Any, Dict, List
from . import store

def post(receipt_id: str, account_id: str = "") -> Dict[str, Any]:
    warnings: List[str] = []
    items = store.list_items()
    r = next((x for x in items if x.get("id") == receipt_id), None)
    if not r:
        raise KeyError("not found")

    cat = r.get("category") or ""
    desc = f"Receipt: {r.get('merchant','')}"
    try:
        from backend.app.core_gov.ledger_light.smart_add import smart_create
        led = smart_create(
            date=r.get("date",""),
            kind="expense",
            amount=float(r.get("total") or 0.0),
            description=desc,
            category=cat,
            account_id=account_id,
        )
    except Exception as e:
        warnings.append(f"ledger post failed: {type(e).__name__}: {e}")
        led = None

    if led is not None:
        try:
            from backend.app.core_gov.receipts import service as rsvc
            rsvc.mark_posted(receipt_id)
        except Exception:
            pass

    return {"ledger": led, "receipt_id": receipt_id, "warnings": warnings}
