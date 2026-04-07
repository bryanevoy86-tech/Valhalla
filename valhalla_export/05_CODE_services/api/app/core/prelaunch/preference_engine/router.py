"""PACK-CORE-PRELAUNCH-01: Preference Engine - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/preferences", tags=["preferences"])


# NOTE: Replace get_current_user_id with your actual auth dependency
# This is a stub that you'll need to implement based on your auth system
async def get_current_user_id() -> UUID:
    """Stub dependency - replace with actual auth implementation"""
    raise NotImplementedError("Replace with your auth system")


@router.get("/me", response_model=schemas.PreferenceProfileRead)
def get_my_prefs(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    profile = service.get_profile_for_user(db, user_id)
    return profile


@router.patch("/me", response_model=schemas.PreferenceProfileRead)
def update_my_prefs(
    payload: schemas.PreferenceProfileUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    profile = service.get_profile_for_user(db, user_id)
    updated = service.update_profile(db, profile, payload)
    return updated
