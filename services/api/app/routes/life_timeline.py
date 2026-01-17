"""
PACK TK: Life Timeline & Milestones Router
Prefix: /timeline
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.life_timeline import (
    LifeEventCreate,
    LifeEventOut,
    LifeMilestoneCreate,
    LifeMilestoneOut,
    LifeTimelineSnapshot,
)
from app.services.life_timeline import (
    create_life_event,
    list_life_events,
    create_life_milestone,
    list_life_milestones,
    get_timeline_snapshot,
)

router = APIRouter(prefix="/timeline", tags=["Life Timeline"])


@router.post("/events", response_model=LifeEventOut)
def create_life_event_endpoint(
    payload: LifeEventCreate,
    db: Session = Depends(get_db),
):
    """Create a life event."""
    return create_life_event(db, payload)


@router.get("/events", response_model=List[LifeEventOut])
def list_life_events_endpoint(
    db: Session = Depends(get_db),
):
    """List all life events."""
    return list_life_events(db)


@router.post("/milestones", response_model=LifeMilestoneOut)
def create_life_milestone_endpoint(
    payload: LifeMilestoneCreate,
    db: Session = Depends(get_db),
):
    """Create a life milestone."""
    return create_life_milestone(db, payload)


@router.get("/milestones", response_model=List[LifeMilestoneOut])
def list_life_milestones_endpoint(
    db: Session = Depends(get_db),
):
    """List all life milestones."""
    return list_life_milestones(db)


@router.get("/snapshot", response_model=LifeTimelineSnapshot)
def get_timeline_snapshot_endpoint(
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """Get timeline snapshot for a date range."""
    return get_timeline_snapshot(db, from_date, to_date)
