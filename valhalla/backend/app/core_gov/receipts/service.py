from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create(payload: Dict[str, Any]) -> Dict[str, Any]:
    vendor = _norm(payload.get("vendor") or "")
    dt = _norm(payload.get("date") or "")
    if not vendor:
        raise ValueError("vendor is required")
    if not dt:
        raise ValueError("date is required (YYYY-MM-DD)")

    now = _utcnow_iso()
    rid = "rc_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "vendor": vendor,
        "date": dt,
        "total": float(payload.get("total") or 0.0),
        "currency": payload.get("currency") or "CAD",
        "status": payload.get("status") or "new",
        "source": payload.get("source") or "manual",
        "tax": float(payload.get("tax") or 0.0),
        "tip": float(payload.get("tip") or 0.0),
        "payment_method": _norm(payload.get("payment_method") or ""),
        "doc_id": _norm(payload.get("doc_id") or ""),
        "blob_ref": _norm(payload.get("blob_ref") or ""),
        "notes": payload.get("notes") or "",
        "category": _norm(payload.get("category") or ""),
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(status: str = "", category: str = "", vendor: str = "", tag: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if category:
        items = [x for x in items if x.get("category") == category]
    if vendor:
        v = vendor.strip().lower()
        items = [x for x in items if (x.get("vendor","").lower().find(v) >= 0)]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    items.sort(key=lambda x: (x.get("date",""), x.get("vendor","")), reverse=True)
    return items[:500]


def get_one(receipt_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == receipt_id:
            return x
    return None


def patch(receipt_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == receipt_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("receipt not found")

    for k in ["vendor","date","currency","status","source","payment_method","doc_id","blob_ref","notes","category"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("vendor","date","payment_method","doc_id","blob_ref","category") else (patch.get(k) or "")
    for k in ["total","tax","tip"]:
        if k in patch:
            tgt[k] = float(patch.get(k) or 0.0)
    if "tags" in patch:
        tgt["tags"] = patch.get("tags") or []
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
