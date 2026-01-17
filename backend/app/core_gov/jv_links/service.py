from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def link(deal_id: str, partner_id: str, role: str = "jv", split_pct: float = 0.0, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    if not (deal_id or "").strip():
        raise ValueError("deal_id required")
    if not (partner_id or "").strip():
        raise ValueError("partner_id required")

    if split_pct < 0 or split_pct > 100:
        raise ValueError("split_pct must be 0..100")

    rec = {
        "id": "jv_" + uuid.uuid4().hex[:12],
        "deal_id": deal_id.strip(),
        "partner_id": partner_id.strip(),
        "role": (role or "jv").strip(),    # jv/buyer/lender/contractor
        "split_pct": float(split_pct or 0.0),
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_links(deal_id: str = "", partner_id: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if deal_id:
        items = [x for x in items if x.get("deal_id") == deal_id]
    if partner_id:
        items = [x for x in items if x.get("partner_id") == partner_id]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:2000]

def split_check(deal_id: str) -> Dict[str, Any]:
    items = [x for x in store.list_items() if x.get("deal_id") == deal_id]
    total = sum(float(x.get("split_pct") or 0.0) for x in items)
    status = "ok" if total <= 100.0 else "over"
    return {"deal_id": deal_id, "total_split_pct": float(total), "status": status, "items": items}
