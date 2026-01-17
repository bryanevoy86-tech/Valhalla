from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(code: str, name: str, risk: str = "safe", notes: str = "", status: str = "active", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    code = (code or "").strip().upper()
    name = (name or "").strip()
    if not code:
        raise ValueError("code required")
    if not name:
        raise ValueError("name required")
    risk = (risk or "safe").strip().lower()
    if risk not in ("safe","aggressive"):
        raise ValueError("risk must be safe|aggressive")

    rec = {
        "id": "txb_" + uuid.uuid4().hex[:12],
        "code": code,
        "name": name,
        "risk": risk,
        "notes": notes or "",
        "status": status,
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def seed_defaults() -> Dict[str, Any]:
    defaults = [
        ("HOME_OFFICE","Home Office","safe"),
        ("VEHICLE","Vehicle/Mileage","safe"),
        ("MARKETING","Marketing/Advertising","safe"),
        ("TOOLS","Tools/Equipment","safe"),
        ("PHONE_INTERNET","Phone/Internet","safe"),
        ("PRO_SERVICES","Professional Services","safe"),
        ("EDUCATION","Training/Education","safe"),
        ("MEALS","Meals (Business)","aggressive"),
    ]
    for c,n,r in defaults:
        create(code=c, name=n, risk=r, notes="seeded", meta={"seed": True})
    return {"seeded": len(defaults)}

def list_items(status: str = "active") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("code",""))
    return items[:5000]
