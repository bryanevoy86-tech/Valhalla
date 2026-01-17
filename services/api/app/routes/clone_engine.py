"""PACK 65: Clone Engine Router
API endpoints for clone profile management and status tracking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.clone_engine_service import create_clone_profile, update_clone_status
from app.schemas.clone_engine import CloneProfileOut

router = APIRouter(prefix="/clone-engine", tags=["Clone Engine"])


@router.post("/", response_model=CloneProfileOut)
def queue_clone(source_zone: str, target_zone: str, include_modules: str, db: Session = Depends(get_db)):
    """Queue a new clone operation."""
    return create_clone_profile(db, source_zone, target_zone, include_modules)


@router.post("/{clone_id}/status", response_model=CloneProfileOut)
def set_clone_status(clone_id: int, status: str, db: Session = Depends(get_db)):
    """Update clone operation status."""
    return update_clone_status(db, clone_id, status)
