"""
PACK SN: Mental Load Offloading Engine Router
FastAPI endpoints for brain externalization and task management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.mental_load import (
    MentalLoadEntrySchema, DailyLoadSummarySchema, LoadOffloadWorkflowSchema,
    MentalLoadResponse
)
from app.services.mental_load import (
    add_mental_load_entry, get_pending_load, get_load_by_category,
    clear_load_entry, create_daily_summary, start_brain_dump_workflow,
    categorize_brain_dump, calculate_cognitive_load
)

router = APIRouter(prefix="/mental-load", tags=["mental-load"])


@router.post("/entries", response_model=MentalLoadEntrySchema)
def add_entry(entry_data: dict, db: Session = Depends(get_db)):
    """Add an item to mental load."""
    return add_mental_load_entry(db, **entry_data)


@router.get("/pending", response_model=list[MentalLoadEntrySchema])
def get_all_pending(db: Session = Depends(get_db)):
    """Get all pending mental load items."""
    return get_pending_load(db)


@router.get("/by-category/{category}", response_model=list[MentalLoadEntrySchema])
def get_by_cat(category: str, db: Session = Depends(get_db)):
    """Get mental load items by category."""
    return get_load_by_category(db, category)


@router.put("/entries/{entry_id}/clear", response_model=MentalLoadEntrySchema)
def mark_clear(entry_id: int, db: Session = Depends(get_db)):
    """Mark a mental load entry as cleared."""
    entry = clear_load_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/daily-summary", response_model=DailyLoadSummarySchema)
def add_daily_summary(summary_data: dict, db: Session = Depends(get_db)):
    """Create a daily load summary."""
    return create_daily_summary(db, **summary_data)


@router.post("/brain-dump", response_model=LoadOffloadWorkflowSchema)
def start_dump(workflow_data: dict, db: Session = Depends(get_db)):
    """Start a rapid brain dump workflow."""
    workflow = start_brain_dump_workflow(db, **workflow_data)
    return workflow


@router.put("/brain-dump/{workflow_id}/categorize", response_model=LoadOffloadWorkflowSchema)
def process_dump(workflow_id: int, categorized_data: dict, db: Session = Depends(get_db)):
    """Categorize brain dump items."""
    workflow = categorize_brain_dump(db, workflow_id, categorized_data.get("items", []))
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/load-status", response_model=MentalLoadResponse)
def get_load_status(db: Session = Depends(get_db)):
    """Get current cognitive load status."""
    metrics = calculate_cognitive_load(db)
    return MentalLoadResponse(
        total_load_items=metrics["total_items"],
        urgent_count=metrics["urgent_count"],
        action_count=metrics["action_count"],
        cleared_today=0,
        cognitive_pressure=metrics["cognitive_pressure"],
        focus_areas=metrics["focus_areas"]
    )
