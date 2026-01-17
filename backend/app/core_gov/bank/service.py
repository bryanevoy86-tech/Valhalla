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
    dt = _norm(payload.get("date") or "")
    desc = _norm(payload.get("description") or "")
    if not dt:
        raise ValueError("date is required (YYYY-MM-DD)")
    if not desc:
        raise ValueError("description is required")

    now = _utcnow_iso()
    tid = "bt_" + uuid.uuid4().hex[:12]
    rec = {
        "id": tid,
        "date": dt,
        "description": desc,
        "amount": float(payload.get("amount") or 0.0),
        "currency": payload.get("currency") or "CAD",
        "txn_type": payload.get("txn_type") or "unknown",
        "account": _norm(payload.get("account") or ""),
        "status": payload.get("status") or "new",
        "external_id": _norm(payload.get("external_id") or ""),
        "tags": payload.get("tags") or [],
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_txns()
    items.append(rec)
    store.save_txns(items)
    return rec


def list_txns(status: str = "", account: str = "", q: str = "", limit: int = 200) -> List[Dict[str, Any]]:
    items = store.list_txns()
    if status:
        items = [x for x in items if x.get("status") == status]
    if account:
        items = [x for x in items if x.get("account") == account]
    if q:
        qq = q.lower().strip()
        items = [x for x in items if qq in (x.get("description","").lower())]
    items.sort(key=lambda x: (x.get("date",""), x.get("id","")), reverse=True)
    return items[: int(limit or 200)]


def get_one(txn_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_txns():
        if x.get("id") == txn_id:
            return x
    return None


def patch(txn_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_txns()
    tgt = None
    for x in items:
        if x.get("id") == txn_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("txn not found")

    for k in ["date","description","currency","txn_type","account","status","external_id","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("date","description","account","external_id") else (patch.get(k) or "")
    if "amount" in patch:
        tgt["amount"] = float(patch.get("amount") or 0.0)
    if "tags" in patch:
        tgt["tags"] = patch.get("tags") or []
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_txns(items)
    return tgt


def bulk_import(payloads: List[Dict[str, Any]], dedupe_external_id: bool = True, max_items: int = 500) -> Dict[str, Any]:
    items = store.list_txns()
    existing_ext = set()
    if dedupe_external_id:
        for x in items:
            eid = (x.get("external_id") or "").strip()
            if eid:
                existing_ext.add(eid)

    created = []
    skipped = 0
    for p in payloads[: int(max_items or 500)]:
        eid = (p.get("external_id") or "").strip()
        if dedupe_external_id and eid and eid in existing_ext:
            skipped += 1
            continue
        try:
            rec = create(p)
            created.append(rec)
            if eid:
                existing_ext.add(eid)
        except Exception:
            skipped += 1

    return {"created": len(created), "skipped": skipped, "items": created[:50]}
