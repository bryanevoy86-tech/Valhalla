from __future__ import annotations
from typing import Any, Dict, List
from . import store

def post(income_id: str, date: str, account_id: str = "") -> Dict[str, Any]:
    warnings: List[str] = []
    items = store.list_items()
    inc = next((x for x in items if x.get("id") == income_id), None)
    if not inc:
        raise KeyError("not found")

    desc = f"Income: {inc.get('name','')}"
    try:
        from ..ledger_light.smart_add import smart_create
        led = smart_create(
            date=date,
            kind="income",
            amount=float(inc.get("amount") or 0.0),
            description=desc,
            category="income",
            account_id=account_id,
        )
    except Exception as e:
        warnings.append(f"ledger unavailable: {type(e).__name__}: {e}")
        led = None

    return {"ledger": led, "income": inc, "warnings": warnings}
