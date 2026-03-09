from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, est_value: float = 0.0, status: str = "listed", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    rec = {
        "id": "tv_" + uuid.uuid4().hex[:12],
        "name": name,
        "status": status,  # listed/sold/archived
        "est_value": float(est_value or 0.0),
        "sold_price": 0.0,
        "sold_date": "",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items

def mark_sold(item_id: str, sold_price: float, sold_date: str, deposit_to_vault_id: str = "", note: str = "") -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")

    tgt["status"] = "sold"
    tgt["sold_price"] = float(sold_price or 0.0)
    tgt["sold_date"] = (sold_date or "").strip()
    tgt["updated_at"] = _utcnow_iso()
    tgt["meta"] = {**(tgt.get("meta") or {}), "sale_note": note or ""}

    store.save_items(items)

    deposit_result = {}
    warnings: List[str] = []
    if deposit_to_vault_id:
        try:
            from backend.app.core_gov.vaults import service as vsvc  # type: ignore
            deposit_result = vsvc.deposit(deposit_to_vault_id, float(sold_price or 0.0), note=f"Tools sale: {tgt.get('name')}")
        except Exception as e:
            warnings.append(f"vault deposit failed: {type(e).__name__}: {e}")

    return {"item": tgt, "deposit_result": deposit_result, "warnings": warnings}
