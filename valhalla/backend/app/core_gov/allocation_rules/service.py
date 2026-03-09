from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, splits: List[Dict[str, Any]], status: str = "active", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    splits: [{vault_id OR vault_name, pct}]
    pct totals should be <= 100 (we allow <100 for leftovers)
    """
    meta = meta or {}
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    if not splits:
        raise ValueError("splits required")

    total = 0.0
    normalized = []
    for s in splits:
        pct = float(s.get("pct") or 0.0)
        if pct < 0 or pct > 100:
            raise ValueError("pct must be 0..100")
        total += pct
        normalized.append({
            "vault_id": (s.get("vault_id") or "").strip(),
            "vault_name": (s.get("vault_name") or "").strip(),
            "pct": pct,
        })
    if total > 100.0:
        raise ValueError("split total must be <= 100")

    rec = {
        "id": "alr_" + uuid.uuid4().hex[:12],
        "name": name,
        "splits": normalized,
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

def list_items(status: str = "active") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("name",""))
    return items[:2000]
