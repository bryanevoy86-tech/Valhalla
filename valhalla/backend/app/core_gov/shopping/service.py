from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(xs: List[str]) -> List[str]:
    out, seen = [], set()
    for x in xs or []:
        x2 = _norm(x)
        if x2 and x2 not in seen:
            seen.add(x2)
            out.append(x2)
    return out


def create_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    now = _utcnow_iso()
    sid = "sh_" + uuid.uuid4().hex[:12]
    rec = {
        "id": sid,
        "name": name,
        "category": payload.get("category") or "other",
        "status": payload.get("status") or "open",
        "priority": payload.get("priority") or "normal",
        "desired_by": _norm(payload.get("desired_by") or ""),
        "qty": float(payload.get("qty") or 1.0),
        "unit": _norm(payload.get("unit") or "count") or "count",
        "est_unit_cost": float(payload.get("est_unit_cost") or 0.0),
        "currency": payload.get("currency") or "CAD",
        "preferred_store": _norm(payload.get("preferred_store") or ""),
        "preferred_brand": _norm(payload.get("preferred_brand") or ""),
        "inventory_item_id": _norm(payload.get("inventory_item_id") or ""),
        "source": _norm(payload.get("source") or "manual") or "manual",
        "tags": _dedupe(payload.get("tags") or []),
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(status: str = "", category: str = "", priority: str = "", tag: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if category:
        items = [x for x in items if x.get("category") == category]
    if priority:
        items = [x for x in items if x.get("priority") == priority]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    # sort: priority then desired_by
    pr = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    items.sort(key=lambda x: (pr.get(x.get("priority","normal"), 2), x.get("desired_by",""), x.get("name","")))
    return items


def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == item_id:
            return x
    return None


def patch_item(item_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")

    for k in ["name","category","status","priority","desired_by","unit","currency","preferred_store","preferred_brand","inventory_item_id","source","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","desired_by","unit","preferred_store","preferred_brand","inventory_item_id","source") else (patch.get(k) or "")
    if "qty" in patch:
        tgt["qty"] = float(patch.get("qty") or 1.0)
    if "est_unit_cost" in patch:
        tgt["est_unit_cost"] = float(patch.get("est_unit_cost") or 0.0)
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt


def mark_purchased(item_id: str, paid_unit_cost: float = 0.0, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    rec = patch_item(item_id, {"status": "purchased", "est_unit_cost": float(paid_unit_cost or 0.0), "meta": meta})
    return rec
