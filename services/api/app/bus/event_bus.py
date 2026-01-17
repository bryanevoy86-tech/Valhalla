# app/bus/event_bus.py
from pydantic import BaseModel
from datetime import datetime
from typing import List

class BusEvent(BaseModel):
    ts: datetime
    sender: str
    channel: str
    message: str
    meta: dict = {}

class EventBus:
    _events: List[BusEvent] = []

    @classmethod
    def send(cls, sender: str, channel: str, message: str, meta=None):
        cls._events.append(
            BusEvent(
                ts=datetime.utcnow(),
                sender=sender,
                channel=channel,
                message=message,
                meta=meta or {},
            )
        )

    @classmethod
    def read_channel(cls, channel: str) -> List[BusEvent]:
        return [e for e in cls._events if e.channel == channel]
