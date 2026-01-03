from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    kind = payload.get("kind")
    if not name:
        raise ValueError("name is required")
    if kind not in ("asset", "liability"):
        raise ValueError("kind must be asset|liability")

    now = _utcnow_iso()
    iid = "nw_" + uuid.uuid4().hex[:12]
    rec = {
        "id": iid,
        "name": name,
        "kind": kind,
        "status": payload.get("status") or "active",
        "value": float(payload.get("value") or 0.0),
        "currency": payload.get("currency") or "CAD",
        "category": _norm(payload.get("category") or "other") or "other",
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: (x.get("kind",""), x.get("category",""), x.get("name","")))
    return items


def patch(item_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")

    for k in ["name","status","currency","category","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","category") else (patch.get(k) or "")
    if "value" in patch:
        tgt["value"] = float(patch.get("value") or 0.0)
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt


def snapshot(note: str = "") -> Dict[str, Any]:
    items = [x for x in store.list_items() if x.get("status") == "active"]
    assets = [x for x in items if x.get("kind") == "asset"]
    liabs = [x for x in items if x.get("kind") == "liability"]

    asset_total = sum(float(x.get("value") or 0.0) for x in assets)
    liab_total = sum(float(x.get("value") or 0.0) for x in liabs)
    net = float(asset_total - liab_total)

    rec = {
        "id": "ns_" + uuid.uuid4().hex[:12],
        "created_at": _utcnow_iso(),
        "asset_total": float(asset_total),
        "liability_total": float(liab_total),
        "net_worth": net,
        "note": note or "",
        "breakdown": {
            "assets": assets,
            "liabilities": liabs,
        },
    }

    snaps = store.list_snaps()
    snaps.append(rec)
    if len(snaps) > 240:
        snaps = snaps[-240:]
    store.save_snaps(snaps)
    return rec


def list_snapshots(limit: int = 25) -> List[Dict[str, Any]]:
    snaps = store.list_snaps()
    snaps.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return snaps[: int(limit or 25)]
