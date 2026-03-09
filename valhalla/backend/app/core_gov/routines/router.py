from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import store
from .runs import start as start_run, list_runs as list_runs_fn, save_runs as save_runs, _utcnow as rnow
from .reminders import push as push_reminders

router = APIRouter(prefix="/core/routines", tags=["core-routines"])

@router.post("")
def create(title: str, freq: str = "weekly", day_of_week: str = "mon", items: List[str] = Body(default=[]), notes: str = ""):
    try:
        return store.create(title=title, freq=freq, day_of_week=day_of_week, items=items, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active", limit: int = 200):
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.post("/{routine_id}/start")
def start(routine_id: str, run_date: str = ""):
    return start_run(routine_id=routine_id, run_date=run_date)

@router.get("/runs")
def runs(status: str = "open", limit: int = 200):
    items = list_runs_fn()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("run_date",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.post("/runs/{run_id}/check")
def check(run_id: str, item: str):
    items = list_runs_fn()
    it = next((x for x in items if x.get("id") == run_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    done = it.get("done") or []
    if item and item not in done:
        done.append(item)
    it["done"] = done
    it["updated_at"] = rnow()
    save_runs(items)
    return it

@router.post("/runs/{run_id}/complete")
def complete(run_id: str):
    items = list_runs_fn()
    it = next((x for x in items if x.get("id") == run_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    it["status"] = "done"
    it["updated_at"] = rnow()
    save_runs(items)
    return it

@router.post("/push_reminders")
def push_ep():
    return push_reminders()
