"""
PACK CI5: Heimdall Tuning Ruleset Service
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.tuning_rules import TuningProfile, TuningConstraint
from app.schemas.tuning_rules import TuningProfileIn, TuningConstraintIn


def upsert_profile(
    db: Session,
    payload: TuningProfileIn,
) -> TuningProfile:
    """Create or update a tuning profile by name."""
    profile = (
        db.query(TuningProfile)
        .filter(TuningProfile.name == payload.name)
        .first()
    )
    if not profile:
        profile = TuningProfile(**payload.model_dump())
        db.add(profile)
    else:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
        profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def list_profiles(db: Session) -> List[TuningProfile]:
    """List all tuning profiles."""
    return (
        db.query(TuningProfile)
        .order_by(TuningProfile.created_at.asc())
        .all()
    )


def add_constraint(
    db: Session,
    payload: TuningConstraintIn,
) -> TuningConstraint:
    """Add a constraint to a tuning profile."""
    constraint = TuningConstraint(**payload.model_dump())
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


def list_constraints_for_profile(
    db: Session,
    profile_id: int,
) -> List[TuningConstraint]:
    """List all constraints for a profile."""
    return (
        db.query(TuningConstraint)
        .filter(TuningConstraint.profile_id == profile_id)
        .order_by(TuningConstraint.created_at.asc())
        .all()
    )
