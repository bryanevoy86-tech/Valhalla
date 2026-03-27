from __future__ import annotations
from typing import Any, Dict

def post_to_ledger(date: str, amount: float, description: str, category: str = "bills", account_id: str = "") -> Dict[str, Any]:
    # Prefer ledger smart add if present, otherwise fallback
    try:
        from backend.app.core_gov.ledger_light.smart_add import smart_create  # type: ignore
        return smart_create(date=date, kind="expense", amount=amount, description=description, category=category, account_id=account_id)
    except Exception:
        from backend.app.core_gov.ledger_light import service as lsvc  # type: ignore
        return lsvc.create(date_str=date, kind="expense", amount=amount, description=description, category=category, account_id=account_id)
