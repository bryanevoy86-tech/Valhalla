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
    iid = "iv_" + uuid.uuid4().hex[:12]
    rec = {
        "id": iid,
        "name": name,
        "location": payload.get("location") or "pantry",
        "unit": payload.get("unit") or "count",
        "on_hand": float(payload.get("on_hand") or 0),
        "min_threshold": float(payload.get("min_threshold") or 0),
        "reorder_qty": float(payload.get("reorder_qty") or 0),
        "cadence_days": int(payload.get("cadence_days") or 0),
        "priority": payload.get("priority") or "normal",
        "preferred_brand": _norm(payload.get("preferred_brand") or ""),
        "preferred_store": _norm(payload.get("preferred_store") or ""),
        "est_unit_cost": float(payload.get("est_unit_cost") or 0.0),
        "tags": _dedupe(payload.get("tags") or []),
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "last_updated": now,
        "last_purchased": "",
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(location: Optional[str] = None, tag: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_items()
    if location:
        items = [x for x in items if x.get("location") == location]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    if priority:
        items = [x for x in items if x.get("priority") == priority]
    items.sort(key=lambda x: (x.get("priority","normal"), x.get("name","")))
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

    for k in ["name","location","unit","priority","preferred_brand","preferred_store","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","preferred_brand","preferred_store") else (patch.get(k) or "")
    for k in ["on_hand","min_threshold","reorder_qty","est_unit_cost"]:
        if k in patch:
            tgt[k] = float(patch.get(k) or 0)
    if "cadence_days" in patch:
        tgt["cadence_days"] = int(patch.get("cadence_days") or 0)
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    now = _utcnow_iso()
    tgt["last_updated"] = now
    tgt["updated_at"] = now
    store.save_items(items)
    return tgt


def adjust_stock(item_id: str, delta: float, reason: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")

    tgt["on_hand"] = float(tgt.get("on_hand") or 0) + float(delta or 0)
    now = _utcnow_iso()
    tgt["last_updated"] = now
    tgt["updated_at"] = now
    if delta and delta > 0:
        tgt["last_purchased"] = now

    store.save_items(items)

    logs = store.list_logs()
    logs.append({
        "id": "il_" + uuid.uuid4().hex[:12],
        "item_id": item_id,
        "delta": float(delta or 0),
        "reason": reason or "",
        "meta": meta,
        "created_at": now,
    })
    if len(logs) > 500:
        logs = logs[-500:]
    store.save_logs(logs)

    return tgt
