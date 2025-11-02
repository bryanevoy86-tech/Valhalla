"""
Telemetry router - logs events and errors for monitoring and debugging.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..schemas.telemetry import TelemetryIn
from ..models.telemetry import TelemetryEvent
from ..core.auth import require_builder_key

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def log_telemetry(
    data: TelemetryIn,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_builder_key)
):
    """
    Log a telemetry event. Requires builder API key authentication.
    
    Use this endpoint to log system events, errors, builds, ingestions, etc.
    """
    event = TelemetryEvent(
        kind=data.kind,
        message=data.message,
        meta_json=data.meta_json
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {
        "ok": True,
        "id": event.id,
        "kind": event.kind,
        "created_at": event.created_at.isoformat()
    }
