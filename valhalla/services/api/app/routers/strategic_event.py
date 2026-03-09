"""
PACK L0-09: Strategic Event Router
Records strategic events from various modules.
Prefix: /api/v1/strategic/events
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.strategic_event import (
    StrategicEventCreate,
    StrategicEventOut,
    StrategicEventList,
)
from app.services import strategic_event as service

router = APIRouter(
    prefix="/api/v1/strategic/events",
    tags=["Strategic Engine", "Events"],
)


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    return "default-tenant"


@router.post("", response_model=StrategicEventOut, status_code=201)
def record_event(
    payload: StrategicEventCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Record a strategic event."""
    return service.record_event(
        db,
        tenant_id=tenant_id,
        source=payload.source,
        category=payload.category,
        label=payload.label,
        payload=payload.payload,
        importance_score=payload.importance_score,
    )


@router.get("", response_model=StrategicEventList)
def list_events(
    source: Optional[str] = Query(None, description="Filter by event source"),
    category: Optional[str] = Query(None, description="Filter by event category"),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List strategic events with filtering."""
    items, total = service.list_events(
        db,
        tenant_id=tenant_id,
        source=source,
        category=category,
        min_importance=min_importance,
        skip=skip,
        limit=limit,
    )
    return StrategicEventList(total=total, items=items)


@router.get("/{event_id}", response_model=StrategicEventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific strategic event."""
    event = service.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Delete a strategic event."""
    success = service.delete_event(db, event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return None
    db: Session = Depends(get_db),
):
    """
    Add a strategic event to the long-term timeline.
    """
    return create_strategic_event(db, payload)


@router.get("/", response_model=StrategicEventList)
def get_events(
    domain: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """
    List strategic events for Heimdall's long-term memory.
    """
    items = list_strategic_events(db, domain=domain, event_type=event_type, limit=limit)
    return StrategicEventList(
        total=len(items),
        items=[StrategicEventOut.model_validate(i) for i in items],
    )
