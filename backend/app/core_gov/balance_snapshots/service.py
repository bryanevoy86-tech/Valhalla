from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(date: str, account_id: str, balance: float, currency: str = "", notes: str = "") -> Dict[str, Any]:
    date = (date or "").strip()
    account_id = (account_id or "").strip()
    if not date:
        raise ValueError("date required (YYYY-MM-DD)")
    if not account_id:
        raise ValueError("account_id required")
    rec = {
        "id": store.new_id(),
        "date": date,
        "account_id": account_id,
        "balance": float(balance or 0.0),
        "currency": (currency or "").strip().upper(),
        "notes": notes or "",
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_recent(account_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(2000, int(limit or 50)))
    items = store.list_items()
    if account_id:
        items = [x for x in items if x.get("account_id") == account_id]
    items.sort(key=lambda x: (x.get("date",""), x.get("created_at","")), reverse=True)
    return items[:limit]
