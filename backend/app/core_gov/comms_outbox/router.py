from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from . import service

router = APIRouter(prefix="/core/comms_outbox", tags=["core-comms-outbox"])

@router.post("")
def create(channel: str, to: str, subject: str = "", body: str = "", entity_type: str = "", entity_id: str = "", status: str = "draft", tags: List[str] = None, notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.create(channel=channel, to=to, subject=subject, body=body, entity_type=entity_type, entity_id=entity_id, status=status, tags=tags, notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", channel: str = "", q: str = ""):
    return {"items": service.list_items(status=status, channel=channel, q=q)}

@router.post("/{msg_id}/sent")
def sent(msg_id: str):
    try:
        return service.mark_sent(msg_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="message not found")
