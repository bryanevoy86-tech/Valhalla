"""
PACK TH: Crisis Management Router
Prefix: /crisis
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.crisis import (
    CrisisProfileCreate,
    CrisisProfileOut,
    CrisisActionStepCreate,
    CrisisActionStepOut,
    CrisisLogCreate,
    CrisisLogOut,
)
from app.services.crisis import (
    create_crisis_profile,
    list_crisis_profiles,
    add_crisis_step,
    create_crisis_log,
    resolve_crisis_log,
)

router = APIRouter(prefix="/crisis", tags=["Crisis"])


@router.post("/profiles", response_model=CrisisProfileOut)
def create_crisis_profile_endpoint(
    payload: CrisisProfileCreate,
    db: Session = Depends(get_db),
):
    """Create a new crisis profile."""
    return create_crisis_profile(db, payload)


@router.get("/profiles", response_model=List[CrisisProfileOut])
def list_crisis_profiles_endpoint(
    db: Session = Depends(get_db),
):
    """List all crisis profiles."""
    return list_crisis_profiles(db)


@router.post("/steps", response_model=CrisisActionStepOut)
def add_crisis_step_endpoint(
    payload: CrisisActionStepCreate,
    db: Session = Depends(get_db),
):
    """Add an action step to a crisis profile."""
    step = add_crisis_step(db, payload)
    if not step:
        raise HTTPException(status_code=404, detail="Crisis profile not found")
    return step


@router.post("/logs", response_model=CrisisLogOut)
def create_crisis_log_endpoint(
    payload: CrisisLogCreate,
    db: Session = Depends(get_db),
):
    """Create a log entry for a crisis."""
    log = create_crisis_log(db, payload)
    if not log:
        raise HTTPException(status_code=404, detail="Crisis profile not found")
    return log


@router.post("/logs/{log_id}/resolve", response_model=CrisisLogOut)
def resolve_crisis_log_endpoint(
    log_id: int,
    db: Session = Depends(get_db),
):
    """Mark a crisis log entry as resolved."""
    log = resolve_crisis_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
