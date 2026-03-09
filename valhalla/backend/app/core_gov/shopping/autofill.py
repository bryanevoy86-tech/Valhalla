from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from . import store as sstore


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_key(item_id: str) -> str:
    return f"inventory_reorder:{item_id}"


def _existing_keys(items: List[Dict[str, Any]]) -> set:
    keys = set()
    for x in items:
        k = (x.get("meta") or {}).get("dedupe_key")
        if k:
            keys.add(k)
    return keys


def create_from_inventory(max_create: int = 25) -> Dict[str, Any]:
    warnings: List[str] = []
    created: List[Dict[str, Any]] = []

    try:
        from backend.app.core_gov.inventory import reorder  # type: ignore
        suggestions = (reorder.suggest_reorders(max_items=max_create) or {}).get("items", [])
    except Exception as e:
        return {"created": 0, "warnings": [f"inventory unavailable: {type(e).__name__}: {e}"], "items": []}

    items = sstore.list_items()
    keys = _existing_keys(items)

    for s in suggestions:
        if len(created) >= int(max_create or 25):
            break
        inv_id = s.get("item_id") or ""
        if not inv_id:
            continue
        dk = _hash_key(inv_id)
        if dk in keys:
            continue

        rec = {
            "id": "sh_" + uuid.uuid4().hex[:12],
            "name": s.get("name") or "Reorder item",
            "category": "household",
            "status": "open",
            "priority": s.get("priority") or "normal",
            "desired_by": "",  # optional
            "qty": float(s.get("reorder_qty") or 1.0),
            "unit": s.get("unit") or "count",
            "est_unit_cost": float(s.get("est_unit_cost") or 0.0),
            "currency": "CAD",
            "preferred_store": s.get("preferred_store") or "",
            "preferred_brand": s.get("preferred_brand") or "",
            "inventory_item_id": inv_id,
            "source": "inventory",
            "tags": ["inventory_reorder"] + (s.get("tags") or []),
            "notes": "",
            "meta": {"dedupe_key": dk, "reorder_snapshot": s},
            "created_at": _utcnow_iso(),
            "updated_at": _utcnow_iso(),
        }
        items.append(rec)
        keys.add(dk)
        created.append(rec)

    sstore.save_items(items)
    return {"created": len(created), "warnings": warnings, "items": created}
