from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(title: str, category: str = "general", priority: str = "normal", desired_by: str = "", est_cost: float = 0.0, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")

    rec = {
        "id": "pr_" + uuid.uuid4().hex[:12],
        "title": title,
        "category": (category or "general").strip() or "general",
        "priority": (priority or "normal").strip() or "normal",
        "desired_by": (desired_by or "").strip(),
        "est_cost": float(est_cost or 0.0),
        "status": "open",  # open/approved/rejected/fulfilled
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:300]

def approve(req_id: str, auto_create_shopping: bool = True, auto_create_reminder: bool = True) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == req_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("request not found")

    tgt["status"] = "approved"
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)

    warnings: List[str] = []
    created = {}

    if auto_create_shopping:
        try:
            from backend.app.core_gov.shopping import service as ssvc  # type: ignore
            created["shopping"] = ssvc.create({
                "name": tgt.get("title",""),
                "qty": 1.0,
                "unit": "each",
                "category": tgt.get("category") or "general",
                "priority": "high" if tgt.get("priority") in ("high","urgent") else "normal",
                "status": "open",
                "desired_by": tgt.get("desired_by",""),
                "est_unit_cost": float(tgt.get("est_cost") or 0.0),
                "notes": "Auto-created from purchase request approval",
                "meta": {"purchase_request_id": req_id},
            })
        except Exception as e:
            warnings.append(f"shopping create failed: {type(e).__name__}: {e}")

    if auto_create_reminder:
        try:
            from backend.app.core_gov.reminders import service as rsvc  # type: ignore
            due = tgt.get("desired_by") or date.today().isoformat()
            created["reminder"] = rsvc.create({
                "title": f"Buy: {tgt.get('title','')}",
                "due_date": due,
                "status": "active",
                "tags": ["purchase_request", tgt.get("category","general")],
                "notes": "Approved purchase request — complete shopping item.",
                "meta": {"purchase_request_id": req_id},
            })
        except Exception as e:
            warnings.append(f"reminder create failed: {type(e).__name__}: {e}")

    return {"request": tgt, "created": created, "warnings": warnings}
