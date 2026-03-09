"""
PACK AH: Event Log / Timeline Engine Router
Prefix: /events
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.event_log import EventLogCreate, EventLogOut
from app.services.event_log import record_event, list_events_for_entity, list_recent_events

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventLogOut)
def record_event_endpoint(
    payload: EventLogCreate,
    db: Session = Depends(get_db),
):
    """Record a new event to the timeline"""
    return record_event(db, payload)


@router.get("/entity", response_model=List[EventLogOut])
def list_entity_events_endpoint(
    entity_type: str = Query(...),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List events for a specific entity type, optionally filtered by entity_id"""
    return list_events_for_entity(db, entity_type=entity_type, entity_id=entity_id, limit=limit)


@router.get("/recent", response_model=List[EventLogOut])
def list_recent_events_endpoint(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List recent events across all entities"""
    return list_recent_events(db, limit=limit)
