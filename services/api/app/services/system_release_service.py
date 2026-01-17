"""PACK 66: System Release Service
Service layer for system release operations.
"""

from sqlalchemy.orm import Session

from app.models.system_release import SystemRelease


def log_release(db: Session, version: str, changelog: str, deployed_by: str) -> SystemRelease:
    """Log a new system release."""
    rel = SystemRelease(
        version=version,
        changelog=changelog,
        deployed_by=deployed_by
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def list_releases(db: Session) -> list:
    """List all system releases in reverse chronological order."""
    return db.query(SystemRelease).order_by(SystemRelease.id.desc()).all()
