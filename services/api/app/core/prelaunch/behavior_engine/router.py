"""PACK-PRELAUNCH-09: Behavior Engine Router"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from . import schemas, service

router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.get("/", response_model=List[schemas.BehaviorRead])
def get_profiles(db: Session = Depends(get_db)):
    """List all behavior profiles."""
    return service.list_profiles(db)


@router.post("/", response_model=schemas.BehaviorRead)
def create_profile(payload: schemas.BehaviorCreate, db: Session = Depends(get_db)):
    """Create a new behavior profile for vetting (lawyer, accountant, contractor, partner, etc.)."""
    return service.create_profile(db, payload)


@router.get("/{profile_id}", response_model=schemas.BehaviorRead)
def get_profile(profile_id: UUID, db: Session = Depends(get_db)):
    """Get a specific behavior profile."""
    profile = service.get_profile(db, str(profile_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=schemas.BehaviorRead)
def update_profile(profile_id: UUID, payload: schemas.BehaviorUpdate, db: Session = Depends(get_db)):
    """Update a behavior profile."""
    try:
        return service.update_profile(db, str(profile_id), payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Profile not found")
