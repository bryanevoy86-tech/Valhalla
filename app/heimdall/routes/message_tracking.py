from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.heimdall.services.message_tracking_service import (
    log_message_delivery,
    log_message_reply,
)

router = APIRouter(
    prefix="/heimdall/message-tracking",
    tags=["Heimdall Message Tracking"],
)


class DeliveryPayload(BaseModel):
    delivery_payload: Dict[str, Any]


class ReplyPayload(BaseModel):
    reply_payload: Dict[str, Any]


@router.post("/{message_id}/delivery")
def delivery(
    message_id: str,
    payload: DeliveryPayload,
    db: Session = Depends(get_db),
):
    return log_message_delivery(
        db=db,
        message_id=message_id,
        delivery_payload=payload.delivery_payload,
    )


@router.post("/{message_id}/reply")
def reply(
    message_id: str,
    payload: ReplyPayload,
    db: Session = Depends(get_db),
):
    return log_message_reply(
        db=db,
        message_id=message_id,
        reply_payload=payload.reply_payload,
    )
