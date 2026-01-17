# app/api/v1/telemetry.py
from fastapi import APIRouter, Depends
from typing import List

from app.auth.dependencies import get_current_admin_user
from app.telemetry.feed import TelemetryFeed, TelemetrySignal

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.get("/signals", response_model=List[TelemetrySignal])
async def get_signals(user=Depends(get_current_admin_user)):
    return TelemetryFeed.read()
