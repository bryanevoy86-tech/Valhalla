from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import service
from .from_bundle import create_from_bundle

router = APIRouter(prefix="/core/outbox", tags=["core-outbox"])

@router.post("")
def create(channel: str, to: str, subject: str = "", body: str = "", related: Dict[str, Any] = Body(default={})):
    try:
        return service.create(channel=channel, to=to, subject=subject, body=body, related=related or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}

@router.post("/{outbox_id}/ready")
def ready(outbox_id: str):
    try:
        return service.mark_ready(outbox_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{outbox_id}/sent")
def sent(outbox_id: str, sent_via: str = "manual"):
    try:
        return service.mark_sent(outbox_id, sent_via=sent_via)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/from_followups")
def from_followups(limit: int = 25):
    from .from_followups import create_from_open
    return create_from_open(limit=limit)

@router.post("/from_bundle")
def from_bundle(bundle_id: str, to: str = "(paste)", channel: str = "email"):
    return create_from_bundle(bundle_id=bundle_id, to=to, channel=channel)

@router.post("/from_deal_script")
def from_deal_script(deal_id: str, channel: str = "sms", to: str = "(paste)", tone: str = "neutral"):
    from .from_scripts import create_from_deal_script
    return create_from_deal_script(deal_id=deal_id, channel=channel, to=to, tone=tone)
