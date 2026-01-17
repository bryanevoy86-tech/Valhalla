from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, bank: str, account_type: str = "chequing", country: str = "CA", currency: str = "CAD", last4: str = "", notes: str = "", meta: Dict[str, Any] = None, status: str = "active") -> Dict[str, Any]:
    meta = meta or {}
    name = (name or "").strip()
    bank = (bank or "").strip()
    if not name:
        raise ValueError("name required")
    if not bank:
        raise ValueError("bank required")

    rec = {
        "id": "acct_" + uuid.uuid4().hex[:12],
        "name": name,
        "bank": bank,
        "account_type": (account_type or "chequing").strip(),  # chequing|savings|credit|line_of_credit
        "country": (country or "CA").strip().upper(),
        "currency": (currency or "CAD").strip().upper(),
        "last4": (last4 or "").strip(),
        "status": status,
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("bank","").lower())]
    items.sort(key=lambda x: (x.get("bank",""), x.get("name","")))
    return items[:2000]

def get_one(account_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == account_id:
            return x
    return None
