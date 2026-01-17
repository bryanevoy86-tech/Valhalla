from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(title: str, target_amount: float, target_date: str = "", vault_id: str = "", vault_name: str = "", priority: str = "normal", notes: str = "", status: str = "active", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")
    if float(target_amount or 0.0) <= 0:
        raise ValueError("target_amount must be > 0")

    rec = {
        "id": "bp_" + uuid.uuid4().hex[:12],
        "title": title,
        "target_amount": float(target_amount),
        "target_date": (target_date or "").strip(),   # YYYY-MM-DD optional
        "vault_id": (vault_id or "").strip(),
        "vault_name": (vault_name or "").strip(),
        "priority": (priority or "normal").strip(),
        "status": status,
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "active", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("title","").lower()) or qq in (x.get("notes","").lower())]
    pr = {"high": 0, "normal": 1, "low": 2}
    items.sort(key=lambda x: (pr.get((x.get("priority") or "normal").lower(), 9), x.get("target_date","")))
    return items[:5000]

def funding_status(purchase_id: str) -> Dict[str, Any]:
    bp = next((x for x in store.list_items() if x.get("id") == purchase_id), None)
    if not bp:
        raise KeyError("purchase not found")

    warnings: List[str] = []
    current = 0.0
    try:
        from backend.app.core_gov.vaults import service as vsvc  # type: ignore
        vid = bp.get("vault_id","")
        if not vid and bp.get("vault_name"):
            # resolve by name
            for v in vsvc.list_items():
                if v.get("name","").lower() == bp.get("vault_name","").lower():
                    vid = v.get("id","")
                    break
        if vid:
            v = vsvc.get_one(vid)
            if v:
                current = float(v.get("balance") or 0.0)
        else:
            warnings.append("vault not linked")
    except Exception as e:
        warnings.append(f"vaults unavailable: {type(e).__name__}: {e}")

    target = float(bp.get("target_amount") or 0.0)
    return {"purchase_id": purchase_id, "title": bp.get("title",""), "target": target, "current": current, "remaining": float(max(0.0, target - current)), "warnings": warnings}
