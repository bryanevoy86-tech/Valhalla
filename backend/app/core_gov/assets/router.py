from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import store
from .warranty import warranty_report
from .maintenance import create as create_maint, list_items as list_maint, save_items as save_maint, _utcnow as mnow
from .replace import add as add_replace, list_items as list_replace, save_items as save_replace, _utcnow as repnow
from .replace_actions import push_replace_to_shopping

router = APIRouter(prefix="/core/assets", tags=["core-assets"])

@router.post("")
def create(name: str, kind: str = "household", purchase_date: str = "", purchase_price: float = 0.0, warranty_months: int = 0, serial: str = "", location: str = "", notes: str = ""):
    try:
        return store.create(name=name, kind=kind, purchase_date=purchase_date, purchase_price=purchase_price, warranty_months=warranty_months, serial=serial, location=location, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(kind: str = "", status: str = "active", limit: int = 200):
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if kind:
        items = [x for x in items if x.get("kind") == kind]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.patch("/{asset_id}")
def patch(asset_id: str, payload: Dict[str, Any] = Body(...)):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == asset_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    p = payload or {}
    for k in ("name","kind","purchase_date","purchase_price","warranty_months","serial","location","notes","status"):
        if k in p:
            it[k] = p[k]
    it["updated_at"] = store._utcnow()  # type: ignore
    store.save_items(items)
    return it

@router.get("/warranty_report")
def warranty_report_ep(limit: int = 50):
    return warranty_report(limit=limit)

@router.post("/maintenance")
def add_maintenance(asset_id: str, title: str, cadence: str = "quarterly", due_date: str = "", notes: str = ""):
    if not asset_id or not title:
        raise HTTPException(status_code=400, detail="asset_id and title required")
    return create_maint(asset_id=asset_id, title=title, cadence=cadence, due_date=due_date, notes=notes)

@router.get("/maintenance")
def list_maintenance(status: str = "open", limit: int = 200):
    items = list_maint()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("due_date",""))
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.post("/maintenance/{mnt_id}/done")
def maintenance_done(mnt_id: str):
    items = list_maint()
    it = next((x for x in items if x.get("id") == mnt_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    it["status"] = "done"
    it["updated_at"] = mnow()
    save_maint(items)
    return it

@router.post("/replace")
def add_replace_ep(title: str, within_days: int = 60, est_cost: float = 0.0, notes: str = ""):
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    return add_replace(title=title, within_days=within_days, est_cost=est_cost, notes=notes)

@router.get("/replace")
def list_replace_ep(status: str = "open", limit: int = 200):
    items = list_replace()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("due",""))
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.post("/replace/push_to_shopping")
def replace_to_shopping(threshold: float = 200.0):
    return push_replace_to_shopping(threshold=threshold)
