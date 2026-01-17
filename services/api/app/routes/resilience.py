"""
PACK TD: Resilience & Recovery Planner Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.resilience import (
    SetbackEventCreate,
    SetbackEventOut,
    RecoveryPlanCreate,
    RecoveryPlanOut,
    RecoveryActionCreate,
    RecoveryActionOut,
)
from app.services.resilience import (
    create_setback_event,
    list_setback_events,
    get_setback_event,
    mark_setback_resolved,
    create_recovery_plan,
    list_recovery_plans,
    get_recovery_plan,
    update_recovery_plan_status,
    add_recovery_action,
    complete_recovery_action,
)

router = APIRouter(prefix="/resilience", tags=["Resilience & Recovery"])


@router.post("/setbacks", response_model=SetbackEventOut)
def post_setback(event: SetbackEventCreate, db: Session = Depends(get_db)):
    """Create a new setback event."""
    return create_setback_event(db, event)


@router.get("/setbacks", response_model=list[SetbackEventOut])
def get_setbacks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all setback events."""
    return list_setback_events(db, skip, limit)


@router.get("/setbacks/{event_id}", response_model=SetbackEventOut)
def get_one_setback(event_id: int, db: Session = Depends(get_db)):
    """Get a specific setback event."""
    db_event = get_setback_event(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Setback event not found")
    return db_event


@router.post("/setbacks/{event_id}/resolve", response_model=SetbackEventOut)
def resolve_setback(event_id: int, db: Session = Depends(get_db)):
    """Mark a setback event as resolved."""
    db_event = mark_setback_resolved(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Setback event not found")
    return db_event


@router.post("/plans", response_model=RecoveryPlanOut)
def post_recovery_plan(plan: RecoveryPlanCreate, db: Session = Depends(get_db)):
    """Create a new recovery plan."""
    # Verify setback exists
    if not get_setback_event(db, plan.setback_id):
        raise HTTPException(status_code=404, detail="Setback event not found")
    return create_recovery_plan(db, plan)


@router.get("/plans", response_model=list[RecoveryPlanOut])
def get_recovery_plans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all recovery plans."""
    return list_recovery_plans(db, skip, limit)


@router.get("/plans/{plan_id}", response_model=RecoveryPlanOut)
def get_one_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific recovery plan."""
    db_plan = get_recovery_plan(db, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")
    return db_plan


@router.post("/plans/{plan_id}/status/{status}")
def update_plan_status(plan_id: int, status: str, db: Session = Depends(get_db)):
    """Update recovery plan status (active, paused, completed)."""
    db_plan = update_recovery_plan_status(db, plan_id, status)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")
    return db_plan


@router.post("/plans/{plan_id}/actions", response_model=RecoveryActionOut)
def post_recovery_action(
    plan_id: int, action: RecoveryActionCreate, db: Session = Depends(get_db)
):
    """Add a recovery action to a plan."""
    # Verify plan exists
    if not get_recovery_plan(db, plan_id):
        raise HTTPException(status_code=404, detail="Recovery plan not found")
    return add_recovery_action(db, action, plan_id)


@router.post("/actions/{action_id}/complete", response_model=RecoveryActionOut)
def complete_action(action_id: int, db: Session = Depends(get_db)):
    """Mark a recovery action as completed."""
    db_action = complete_recovery_action(db, action_id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Recovery action not found")
    return db_action
