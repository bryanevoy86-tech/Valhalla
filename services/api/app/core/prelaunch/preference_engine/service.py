"""PACK-CORE-PRELAUNCH-01: Preference Engine - Service"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def get_profile_for_user(db: Session, user_id: UUID) -> models.PreferenceProfile:
    profile = (
        db.query(models.PreferenceProfile)
        .filter(models.PreferenceProfile.user_id == user_id)
        .first()
    )
    if not profile:
        profile = models.PreferenceProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(
    db: Session, profile: models.PreferenceProfile, data: schemas.PreferenceProfileUpdate
) -> models.PreferenceProfile:
    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
