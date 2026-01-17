from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(name: str, target: float = 0.0, balance: float = 0.0, category: str = "general", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")

    rec = {
        "id": "v_" + uuid.uuid4().hex[:12],
        "name": name,
        "category": (category or "general").strip() or "general",
        "target": float(target or 0.0),
        "balance": float(balance or 0.0),
        "currency": "CAD",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items() -> List[Dict[str, Any]]:
    items = store.list_items()
    items.sort(key=lambda x: (x.get("category",""), x.get("name","")))
    return items


def get_one(vault_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == vault_id:
            return x
    return None


def patch(vault_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == vault_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("vault not found")

    for k in ["name","category","notes"]:
        if k in patch:
            tgt[k] = (patch.get(k) or "").strip()
    for k in ["target","balance"]:
        if k in patch:
            tgt[k] = float(patch.get(k) or 0.0)
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt


def deposit(vault_id: str, amount: float, note: str = "") -> Dict[str, Any]:
    v = get_one(vault_id)
    if not v:
        raise KeyError("vault not found")
    return patch(vault_id, {"balance": float(v.get("balance") or 0.0) + float(amount or 0.0), "meta": {**(v.get("meta") or {}), "last_txn": {"type": "deposit", "amount": amount, "note": note}}})


def withdraw(vault_id: str, amount: float, note: str = "") -> Dict[str, Any]:
    v = get_one(vault_id)
    if not v:
        raise KeyError("vault not found")
    return patch(vault_id, {"balance": float(v.get("balance") or 0.0) - float(amount or 0.0), "meta": {**(v.get("meta") or {}), "last_txn": {"type": "withdraw", "amount": amount, "note": note}}})
