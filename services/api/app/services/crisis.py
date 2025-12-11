"""
PACK TH: Crisis Management Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.crisis import CrisisProfile, CrisisActionStep, CrisisLogEntry
from app.schemas.crisis import (
    CrisisProfileCreate,
    CrisisActionStepCreate,
    CrisisLogCreate,
)


def create_crisis_profile(db: Session, payload: CrisisProfileCreate) -> CrisisProfile:
    obj = CrisisProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_crisis_profiles(db: Session) -> List[CrisisProfile]:
    return db.query(CrisisProfile).order_by(CrisisProfile.name.asc()).all()


def add_crisis_step(db: Session, payload: CrisisActionStepCreate) -> Optional[CrisisActionStep]:
    crisis = db.query(CrisisProfile).filter(CrisisProfile.id == payload.crisis_id).first()
    if not crisis:
        return None
    obj = CrisisActionStep(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_crisis_log(db: Session, payload: CrisisLogCreate) -> Optional[CrisisLogEntry]:
    crisis = db.query(CrisisProfile).filter(CrisisProfile.id == payload.crisis_id).first()
    if not crisis:
        return None
    obj = CrisisLogEntry(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def resolve_crisis_log(db: Session, log_id: int) -> Optional[CrisisLogEntry]:
    obj = db.query(CrisisLogEntry).filter(CrisisLogEntry.id == log_id).first()
    if not obj:
        return None
    obj.active = False
    db.commit()
    db.refresh(obj)
    return obj
