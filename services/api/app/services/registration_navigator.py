"""
PACK SB: Business Registration Navigator Services
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.registration_navigator import RegistrationFlowStep, RegistrationStageTracker
from app.schemas.registration_navigator import (
    RegistrationFlowStepSchema,
    RegistrationStageTrackerSchema,
    StageProgressResponse,
)


# Stage progression order
STAGE_ORDER = ["preparation", "structure", "documents", "filing", "post_registration"]


def create_flow_step(db: Session, step: RegistrationFlowStepSchema) -> RegistrationFlowStep:
    """Create a registration workflow step."""
    db_step = RegistrationFlowStep(
        step_id=step.step_id,
        category=step.category,
        description=step.description,
        required_documents=step.required_documents,
        status=step.status,
        notes=step.notes,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def get_flow_steps_by_category(db: Session, category: str) -> List[RegistrationFlowStep]:
    """Get all steps in a category."""
    return db.query(RegistrationFlowStep).filter(RegistrationFlowStep.category == category).all()


def create_tracker(db: Session) -> RegistrationStageTracker:
    """Create a new registration stage tracker."""
    tracker = RegistrationStageTracker(current_stage="preparation")
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    return tracker


def get_tracker(db: Session, tracker_id: int) -> Optional[RegistrationStageTracker]:
    """Get a registration tracker by ID."""
    return db.query(RegistrationStageTracker).filter(
        RegistrationStageTracker.id == tracker_id
    ).first()


def update_tracker_stage(
    db: Session, tracker_id: int, new_stage: str
) -> Optional[RegistrationStageTracker]:
    """Move tracker to a new stage."""
    tracker = get_tracker(db, tracker_id)
    if not tracker or new_stage not in STAGE_ORDER:
        return None
    
    tracker.current_stage = new_stage
    db.commit()
    db.refresh(tracker)
    return tracker


def record_business_name(db: Session, tracker_id: int, name: str) -> Optional[RegistrationStageTracker]:
    """Record the business name (Stage 1)."""
    tracker = get_tracker(db, tracker_id)
    if not tracker:
        return None
    
    tracker.business_name = name
    db.commit()
    db.refresh(tracker)
    return tracker


def record_structure_selection(
    db: Session, tracker_id: int, structure: str, notes: str = None
) -> Optional[RegistrationStageTracker]:
    """Record user's selected business structure (Stage 2, non-directive)."""
    tracker = get_tracker(db, tracker_id)
    if not tracker:
        return None
    
    tracker.selected_structure = structure
    tracker.structure_notes = notes or f"User selected: {structure}"
    db.commit()
    db.refresh(tracker)
    return tracker


def get_stage_progress(db: Session, tracker_id: int) -> Optional[StageProgressResponse]:
    """Calculate overall registration progress."""
    tracker = get_tracker(db, tracker_id)
    if not tracker:
        return None
    
    current_idx = STAGE_ORDER.index(tracker.current_stage)
    completed_stages = STAGE_ORDER[:current_idx]
    next_stage_idx = current_idx + 1
    next_stage = STAGE_ORDER[next_stage_idx] if next_stage_idx < len(STAGE_ORDER) else None
    
    progress = (current_idx / len(STAGE_ORDER)) * 100
    
    # Determine missing items based on current stage
    missing = []
    if tracker.current_stage == "preparation" and not tracker.business_name:
        missing.append("Business name required")
    if tracker.current_stage in ["structure", "documents", "filing"] and not tracker.selected_structure:
        missing.append("Business structure selection required")
    
    return StageProgressResponse(
        current_stage=tracker.current_stage,
        completed_stages=completed_stages,
        next_stage=next_stage or "complete",
        progress_percentage=progress,
        missing_items=missing,
    )
