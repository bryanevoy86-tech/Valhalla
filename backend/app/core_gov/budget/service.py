from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _month_key(d: Optional[date] = None) -> str:
    dd = d or date.today()
    return f"{dd.year:04d}-{dd.month:02d}"


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def create_bucket(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    now = _utcnow_iso()
    bid = "bk_" + uuid.uuid4().hex[:12]
    rec = {
        "id": bid,
        "name": name,
        "bucket_type": payload.get("bucket_type") or "variable",
        "status": payload.get("status") or "active",
        "priority": payload.get("priority") or "B",
        "monthly_limit": float(payload.get("monthly_limit") or 0.0),
        "rollover": bool(payload.get("rollover", False)),
        "currency": _norm(payload.get("currency") or "CAD") or "CAD",
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_buckets()
    items.append(rec)
    store.save_buckets(items)
    return rec


def list_buckets(status: Optional[str] = None, bucket_type: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_buckets()
    if status:
        items = [x for x in items if x.get("status") == status]
    if bucket_type:
        items = [x for x in items if x.get("bucket_type") == bucket_type]
    return items


def get_bucket(bucket_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_buckets():
        if x["id"] == bucket_id:
            return x
    return None


def patch_bucket(bucket_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_buckets()
    tgt = None
    for x in items:
        if x["id"] == bucket_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("bucket not found")

    for k in ["name","bucket_type","status","priority","currency"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","currency") else patch.get(k)

    if "monthly_limit" in patch:
        tgt["monthly_limit"] = float(patch.get("monthly_limit") or 0.0)
    if "rollover" in patch:
        tgt["rollover"] = bool(patch.get("rollover"))
    if "notes" in patch:
        tgt["notes"] = patch.get("notes") or ""
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_buckets(items)
    return tgt


def _snapshot_key(month: str, bucket_id: str) -> str:
    return f"{month}::{bucket_id}"


def _load_snapshot_map() -> Dict[str, Dict[str, Any]]:
    m: Dict[str, Dict[str, Any]] = {}
    for s in store.list_snapshots():
        m[_snapshot_key(s["month"], s["bucket_id"])] = s
    return m


def _save_snapshot_map(m: Dict[str, Dict[str, Any]]) -> None:
    store.save_snapshots(list(m.values()))


def set_allocation(month: str, bucket_id: str, allocated: float) -> Dict[str, Any]:
    if not month or len(month) != 7 or month[4] != "-":
        raise ValueError("month must be YYYY-MM")
    if not get_bucket(bucket_id):
        raise KeyError("bucket not found")

    snap_map = _load_snapshot_map()
    key = _snapshot_key(month, bucket_id)
    now = _utcnow_iso()
    s = snap_map.get(key) or {
        "month": month,
        "bucket_id": bucket_id,
        "allocated": 0.0,
        "spent": 0.0,
        "remaining": 0.0,
        "updated_at": now,
    }
    s["allocated"] = float(allocated or 0.0)
    # remaining recompute uses allocated if set, else uses monthly_limit (handled in get_month)
    s["updated_at"] = now
    snap_map[key] = s
    _save_snapshot_map(snap_map)
    return s


def get_month(month: Optional[str] = None) -> List[Dict[str, Any]]:
    month = month or _month_key()
    buckets = [b for b in store.list_buckets() if b.get("status") == "active"]
    snap_map = _load_snapshot_map()
    out: List[Dict[str, Any]] = []
    now = _utcnow_iso()

    for b in buckets:
        key = _snapshot_key(month, b["id"])
        s = snap_map.get(key) or {
            "month": month,
            "bucket_id": b["id"],
            "allocated": 0.0,
            "spent": 0.0,
            "remaining": 0.0,
            "updated_at": now,
        }

        # effective limit: allocated (if >0) else monthly_limit
        limit = float(s.get("allocated") or 0.0)
        if limit <= 0.0:
            limit = float(b.get("monthly_limit") or 0.0)

        spent = float(s.get("spent") or 0.0)
        s["remaining"] = round(limit - spent, 2)
        s["updated_at"] = now
        snap_map[key] = s
        out.append(s)

    _save_snapshot_map(snap_map)
    out.sort(key=lambda x: x["bucket_id"])
    return out
