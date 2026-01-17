from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import store
from .audit import audit
from .reminders import push

router = APIRouter(prefix="/core/subscriptions", tags=["core-subscriptions"])

@router.post("")
def create(name: str, amount: float, cadence: str = "monthly", currency: str = "CAD", renewal_day: int = 1, category: str = "subscriptions", notes: str = ""):
    try:
        return store.create(name=name, amount=amount, cadence=cadence, currency=currency, renewal_day=renewal_day, category=category, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active", limit: int = 200):
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.patch("/{sub_id}")
def patch(sub_id: str, payload: Dict[str, Any] = Body(...)):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == sub_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    p = payload or {}
    for k in ("name","amount","currency","cadence","renewal_day","category","notes","status"):
        if k in p:
            it[k] = p[k]
    it["updated_at"] = store._utcnow()  # type: ignore
    store.save_items(items)
    return it

@router.get("/audit")
def audit_ep():
    return audit()

@router.post("/push_reminders")
def push_ep(days_ahead: int = 7):
    return push(days_ahead=days_ahead)
