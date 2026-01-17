"""
PACK TN: Trust & Relationship Mapping Router
Prefix: /relationships
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.relationships import (
    RelationshipProfileCreate,
    RelationshipProfileOut,
    TrustEventCreate,
    TrustEventOut,
    RelationshipMapSnapshot,
)
from app.services.relationships import (
    create_relationship_profile,
    list_relationship_profiles,
    create_trust_event,
    list_trust_events,
    get_relationship_snapshot,
)

router = APIRouter(prefix="/relationships", tags=["Relationships"])


@router.post("/profiles", response_model=RelationshipProfileOut)
def create_profile_endpoint(
    payload: RelationshipProfileCreate,
    db: Session = Depends(get_db),
):
    return create_relationship_profile(db, payload)


@router.get("/profiles", response_model=list[RelationshipProfileOut])
def list_profiles_endpoint(db: Session = Depends(get_db)):
    return list_relationship_profiles(db)


@router.post("/events", response_model=TrustEventOut)
def create_trust_event_endpoint(
    payload: TrustEventCreate,
    db: Session = Depends(get_db),
):
    ev = create_trust_event(db, payload)
    if not ev:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ev


@router.get("/events", response_model=list[TrustEventOut])
def list_events_endpoint(db: Session = Depends(get_db)):
    return list_trust_events(db)


@router.get("/snapshot", response_model=RelationshipMapSnapshot)
def snapshot_endpoint(db: Session = Depends(get_db)):
    return get_relationship_snapshot(db)
