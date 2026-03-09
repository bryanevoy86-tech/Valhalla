from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from . import service

router = APIRouter(prefix="/core/entity_tracker", tags=["core-entity-tracker"])

@router.post("/entities")
def create_entity(entity_type: str, name: str, country: str = "CA", region_code: str = "", status: str = "active", notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.create_entity(entity_type=entity_type, name=name, country=country, region_code=region_code, status=status, notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/entities")
def list_entities(status: str = "", entity_type: str = "", q: str = ""):
    return {"items": service.list_entities(status=status, entity_type=entity_type, q=q)}

@router.post("/tasks")
def add_task(entity_id: str, title: str, status: str = "open", due_date: str = "", priority: str = "normal", requires_doc: bool = False, notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.add_task(entity_id=entity_id, title=title, status=status, due_date=due_date, priority=priority, requires_doc=requires_doc, notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks")
def list_tasks(entity_id: str = "", status: str = "", q: str = ""):
    return {"items": service.list_tasks(entity_id=entity_id, status=status, q=q)}

@router.post("/tasks/{task_id}/status")
def set_task_status(task_id: str, status: str):
    try:
        return service.set_task_status(task_id=task_id, status=status)
    except KeyError:
        raise HTTPException(status_code=404, detail="task not found")
