"""PACK-CORE-PRELAUNCH-01: Unified Log - Router"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import models, schemas, service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[schemas.SystemEventRead])
def get_events(
    event_type: Optional[models.EventType] = None,
    source: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    return service.list_events(db=db, event_type=event_type, source=source, limit=limit)
