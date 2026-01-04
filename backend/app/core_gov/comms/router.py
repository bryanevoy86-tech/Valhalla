from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import MessageCreate, MessageListResponse, MarkSentRequest
from . import service
from .send_log import mark_sent as mark_sent_log
from .deal_message import build as build_deal_message

router = APIRouter(prefix="/core/comms", tags=["core-comms"])


@router.post("")
def create(payload: MessageCreate):
    try:
        return service.create_message(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=MessageListResponse)
def list_messages(status: Optional[str] = None, channel: Optional[str] = None, deal_id: Optional[str] = None):
    return {"items": service.list_messages(status=status, channel=channel, deal_id=deal_id)}


@router.get("/{msg_id}")
def get_one(msg_id: str):
    x = service.get_message(msg_id)
    if not x:
        raise HTTPException(status_code=404, detail="message not found")
    return x


@router.patch("/{msg_id}")
def patch(msg_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_message(msg_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="message not found")


@router.post("/{msg_id}/mark_sent")
def mark_sent(msg_id: str, payload: MarkSentRequest):
    try:
        return service.mark_sent(msg_id, sent_at=payload.sent_at, meta=payload.meta)
    except KeyError:
        raise HTTPException(status_code=404, detail="message not found")

@router.post("/drafts/{draft_id}/sent")
def sent(draft_id: str, channel: str = "", result: str = "sent"):
    try:
        return mark_sent_log(draft_id=draft_id, channel=channel, result=result)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.get("/deal/{deal_id}/build")
def build_for_deal(deal_id: str, kind: str = "sms", tone: str = "neutral"):
    return build_deal_message(deal_id=deal_id, kind=kind, tone=tone)