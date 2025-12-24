from __future__ import annotations

from fastapi import APIRouter
from .schemas import TelemetryEventIn

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# NOTE: This is an API-only stub for now.
# When you want DB persistence, we add models + Alembic.
# For viability, this still lets you post telemetry from workers and engines.


@router.post("/event")
def ingest_event(evt: TelemetryEventIn):
    return {"ok": True, "received": evt.model_dump()}
