"""PACK-PRELAUNCH-09: Behavior Engine Service"""
from typing import List
from sqlalchemy.orm import Session

from . import models, schemas


def create_profile(db: Session, data: schemas.BehaviorCreate) -> models.BehaviorProfile:
    """Create a new behavior profile."""
    profile = models.BehaviorProfile(**data.dict())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def list_profiles(db: Session) -> List[models.BehaviorProfile]:
    """List all behavior profiles ordered by creation date."""
    return db.query(models.BehaviorProfile).order_by(models.BehaviorProfile.created_at.desc()).all()


def get_profile(db: Session, profile_id: str) -> models.BehaviorProfile | None:
    """Get a specific behavior profile by ID."""
    return db.query(models.BehaviorProfile).filter(models.BehaviorProfile.id == profile_id).first()


def update_profile(db: Session, profile_id: str, data: schemas.BehaviorUpdate) -> models.BehaviorProfile:
    """Update a behavior profile."""
    profile = get_profile(db, profile_id)
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")
    
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile
