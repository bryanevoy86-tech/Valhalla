from typing import Dict, Any

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.logging.service import LoggingService
from app.logging.schemas import LogEntry
from app.core.db import get_db


router = APIRouter(prefix="/logging", tags=["logging"])


@router.post("/log", response_model=LogEntry)
async def log_action(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    user_id = str(payload.get("user_id", "unknown"))
    action = str(payload.get("action", "unknown"))
    details = str(payload.get("details", ""))
    return LoggingService(db).log_action(user_id, action, details)
