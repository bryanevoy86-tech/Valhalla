from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from . import service

router = APIRouter(prefix="/core/comms_templates", tags=["core-comms-templates"])

@router.post("")
def create(name: str, channel: str, subject: str = "", body: str = "", tags: List[str] = None, status: str = "active", notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.create(name=name, channel=channel, subject=subject, body=body, tags=tags, status=status, notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", channel: str = "", tag: str = "", q: str = ""):
    return {"items": service.list_items(status=status, channel=channel, tag=tag, q=q)}

@router.post("/{tpl_id}/render")
def render(tpl_id: str, variables: Dict[str, Any]):
    tpl = service.get_one(tpl_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="template not found")
    return service.render(tpl, variables)
