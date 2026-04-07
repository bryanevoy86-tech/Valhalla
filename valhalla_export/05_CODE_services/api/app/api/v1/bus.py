# app/api/v1/bus.py
from fastapi import APIRouter, Depends
from typing import List

from app.auth.dependencies import get_current_admin_user
from app.bus.event_bus import EventBus, BusEvent

router = APIRouter(prefix="/bus", tags=["event_bus"])

@router.post("/send")
async def send_event(
    sender: str,
    channel: str,
    message: str,
    user=Depends(get_current_admin_user)
):
    EventBus.send(sender, channel, message)
    return {"status": "sent"}

@router.get("/channel/{channel}", response_model=List[BusEvent])
async def read_channel(channel: str, user=Depends(get_current_admin_user)):
    return EventBus.read_channel(channel)
