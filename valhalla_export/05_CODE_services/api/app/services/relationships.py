"""
PACK TN: Trust & Relationship Mapping Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.relationships import RelationshipProfile, TrustEventLog
from app.schemas.relationships import (
    RelationshipProfileCreate,
    TrustEventCreate,
    RelationshipMapSnapshot,
)


def create_relationship_profile(
    db: Session,
    payload: RelationshipProfileCreate,
) -> RelationshipProfile:
    obj = RelationshipProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_relationship_profiles(db: Session) -> List[RelationshipProfile]:
    return db.query(RelationshipProfile).order_by(RelationshipProfile.name.asc()).all()


def create_trust_event(db: Session, payload: TrustEventCreate) -> Optional[TrustEventLog]:
    profile = (
        db.query(RelationshipProfile)
        .filter(RelationshipProfile.id == payload.profile_id)
        .first()
    )
    if not profile:
        return None
    obj = TrustEventLog(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_trust_events(db: Session) -> List[TrustEventLog]:
    return db.query(TrustEventLog).order_by(TrustEventLog.date.desc()).all()


def get_relationship_snapshot(db: Session) -> RelationshipMapSnapshot:
    profiles = list_relationship_profiles(db)
    events = list_trust_events(db)
    return RelationshipMapSnapshot(
        profiles=profiles,
        trust_events=events,
    )
