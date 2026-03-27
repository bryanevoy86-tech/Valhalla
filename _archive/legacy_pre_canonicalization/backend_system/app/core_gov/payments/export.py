from __future__ import annotations
from typing import Any, Dict
from . import store
from .service import schedule as sched

def export(days: int = 90) -> Dict[str, Any]:
    items = store.list_items()
    upcoming = sched(items, days=days)

    try:
        from backend.app.core_gov.pay_confirm import store as cstore  # type: ignore
        conf = cstore.list_items()
    except Exception:
        conf = []

    return {"payments": items, "upcoming": upcoming, "confirmations": conf}
