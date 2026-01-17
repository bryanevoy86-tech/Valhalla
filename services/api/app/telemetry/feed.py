# app/telemetry/feed.py
from datetime import datetime
from typing import List
from pydantic import BaseModel

class TelemetrySignal(BaseModel):
    ts: datetime
    source: str
    signal: str
    severity: str = "info"
    meta: dict = {}

class TelemetryFeed:
    _buffer: List[TelemetrySignal] = []

    @classmethod
    def publish(cls, source: str, signal: str, severity: str = "info", meta=None):
        cls._buffer.append(
            TelemetrySignal(
                ts=datetime.utcnow(),
                source=source,
                signal=signal,
                severity=severity,
                meta=meta or {},
            )
        )

    @classmethod
    def read(cls) -> List[TelemetrySignal]:
        return list(cls._buffer)
