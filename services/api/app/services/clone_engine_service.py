"""PACK 65: Clone Engine Service
Service layer for clone profile operations.
"""

from sqlalchemy.orm import Session

from app.models.clone_engine import CloneProfile


def create_clone_profile(db: Session, source_zone: str, target_zone: str, include_modules: str) -> CloneProfile:
    """Create a new clone profile."""
    cp = CloneProfile(
        source_zone=source_zone,
        target_zone=target_zone,
        include_modules=include_modules,
        status="queued"
    )
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


def update_clone_status(db: Session, clone_id: int, status: str) -> CloneProfile:
    """Update clone profile status."""
    cp = db.query(CloneProfile).filter(CloneProfile.id == clone_id).first()
    if cp:
        cp.status = status
        db.commit()
        db.refresh(cp)
    return cp
