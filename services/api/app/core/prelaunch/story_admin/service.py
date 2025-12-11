"""Story Admin Service"""
from typing import List
from sqlalchemy.orm import Session

from . import models, schemas


def get_settings(db: Session) -> models.StorySettings:
    """Get story settings, creating defaults if none exist."""
    settings = db.query(models.StorySettings).first()
    if not settings:
        settings = models.StorySettings(
            default_length_minutes=20,
            allow_comedy=True,
            allow_action=True,
            allow_emotional_focus=True,
            learning_focus=["morals", "problem_solving"],
            bedtime_soft_mode=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(
    db: Session, data: schemas.StorySettingsUpdate
) -> models.StorySettings:
    """Update story settings."""
    settings = get_settings(db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(settings, field, value)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def list_sessions(db: Session, limit: int = 100) -> List[models.StorySession]:
    """List story sessions, newest first."""
    return (
        db.query(models.StorySession)
        .order_by(models.StorySession.created_at.desc())
        .limit(limit)
        .all()
    )


def get_session(db: Session, session_id) -> models.StorySession | None:
    """Get a specific story session."""
    return (
        db.query(models.StorySession)
        .filter(models.StorySession.id == session_id)
        .first()
    )
