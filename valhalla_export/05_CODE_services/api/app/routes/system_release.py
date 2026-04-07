"""PACK 66: System Release Router
API endpoints for version tracking and release management.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.system_release import SystemReleaseOut
from app.services.system_release_service import log_release, list_releases

router = APIRouter(prefix="/release", tags=["System Release"])


@router.post("/", response_model=SystemReleaseOut)
def new_release(version: str, changelog: str, deployed_by: str, db: Session = Depends(get_db)):
    """Log a new system release."""
    return log_release(db, version, changelog, deployed_by)


@router.get("/", response_model=list[SystemReleaseOut])
def get_releases(db: Session = Depends(get_db)):
    """Get all system releases."""
    return list_releases(db)
