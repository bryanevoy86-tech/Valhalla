"""
PACK SB: Business Registration Navigator Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.schemas.registration_navigator import (
    RegistrationFlowStepSchema,
    RegistrationStageTrackerSchema,
    StageProgressResponse,
)
from app.services.registration_navigator import (
    create_flow_step,
    get_flow_steps_by_category,
    create_tracker,
    get_tracker,
    update_tracker_stage,
    record_business_name,
    record_structure_selection,
    get_stage_progress,
)

router = APIRouter(prefix="/registration", tags=["PACK SB: Business Registration Navigator"])


@router.post("/steps", response_model=RegistrationFlowStepSchema)
def create_step(step: RegistrationFlowStepSchema, db: Session = Depends(get_db)):
    """Create a registration workflow step."""
    return create_flow_step(db, step)


@router.get("/steps/category/{category}", response_model=List[RegistrationFlowStepSchema])
def get_steps_for_category(category: str, db: Session = Depends(get_db)):
    """Get all steps in a registration category."""
    return get_flow_steps_by_category(db, category)


@router.post("/tracker", response_model=RegistrationStageTrackerSchema)
def create_new_tracker(db: Session = Depends(get_db)):
    """Start a new business registration tracker."""
    return create_tracker(db)


@router.get("/tracker/{tracker_id}", response_model=RegistrationStageTrackerSchema)
def get_tracker_info(tracker_id: int, db: Session = Depends(get_db)):
    """Get registration tracker details."""
    tracker = get_tracker(db, tracker_id)
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return tracker


@router.post("/tracker/{tracker_id}/stage/{stage}")
def advance_stage(tracker_id: int, stage: str, db: Session = Depends(get_db)):
    """Move tracker to a new stage."""
    updated = update_tracker_stage(db, tracker_id, stage)
    if not updated:
        raise HTTPException(status_code=404, detail="Tracker not found or invalid stage")
    return {"status": "advanced", "new_stage": stage}


@router.post("/tracker/{tracker_id}/business-name")
def set_business_name(tracker_id: int, name: str, db: Session = Depends(get_db)):
    """Record the business name (Stage 1)."""
    updated = record_business_name(db, tracker_id, name)
    if not updated:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return {"status": "recorded", "business_name": name}


@router.post("/tracker/{tracker_id}/structure")
def set_structure(tracker_id: int, structure: str, notes: str = None, db: Session = Depends(get_db)):
    """Record the selected business structure (Stage 2)."""
    updated = record_structure_selection(db, tracker_id, structure, notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return {"status": "recorded", "selected_structure": structure}


@router.get("/tracker/{tracker_id}/progress", response_model=StageProgressResponse)
def get_progress(tracker_id: int, db: Session = Depends(get_db)):
    """Get overall registration progress."""
    progress = get_stage_progress(db, tracker_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return progress
