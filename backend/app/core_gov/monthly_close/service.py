from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def close(month: str) -> Dict[str, Any]:
    """
    month: YYYY-MM
    """
    if not (month or "").strip():
        raise ValueError("month required (YYYY-MM)")
    date_from = month + "-01"
    date_to = month + "-31"

    warnings: List[str] = []
    ledger_summary = {}
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
        ledger_summary = lsvc.summary(date_from=date_from, date_to=date_to)
    except Exception as e:
        warnings.append(f"ledger unavailable: {type(e).__name__}: {e}")
        ledger_summary = {"income": 0.0, "expense": 0.0, "net": 0.0, "count": 0}

    buffer = {}
    try:
        from backend.app.core_gov.bills_buffer import service as bbsvc  # type: ignore
        buffer = bbsvc.required_buffer(days=30)
    except Exception as e:
        warnings.append(f"bills_buffer unavailable: {type(e).__name__}: {e}")
        buffer = {"required": 0.0}

    rec = {
        "id": "mcl_" + uuid.uuid4().hex[:12],
        "month": month.strip(),
        "ledger": ledger_summary,
        "bills_buffer": buffer,
        "warnings": warnings,
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items() -> List[Dict[str, Any]]:
    items = store.list_items()
    items.sort(key=lambda x: x.get("month",""), reverse=True)
    return items[:500]
