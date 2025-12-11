"""
PACK TD: Resilience & Recovery Planner Service Layer
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.resilience import SetbackEvent, RecoveryPlan, RecoveryAction
from app.schemas.resilience import (
    SetbackEventCreate,
    RecoveryPlanCreate,
    RecoveryActionCreate,
)


def create_setback_event(db: Session, event: SetbackEventCreate) -> SetbackEvent:
    """Create a new setback event."""
    db_event = SetbackEvent(
        title=event.title,
        category=event.category,
        description=event.description,
        severity=event.severity,
        date=datetime.utcnow(),
        resolved=False,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def list_setback_events(db: Session, skip: int = 0, limit: int = 100) -> list[SetbackEvent]:
    """List all setback events."""
    return db.query(SetbackEvent).offset(skip).limit(limit).all()


def get_setback_event(db: Session, event_id: int) -> SetbackEvent | None:
    """Get a specific setback event by ID."""
    return db.query(SetbackEvent).filter(SetbackEvent.id == event_id).first()


def mark_setback_resolved(db: Session, event_id: int) -> SetbackEvent | None:
    """Mark a setback event as resolved."""
    db_event = db.query(SetbackEvent).filter(SetbackEvent.id == event_id).first()
    if db_event:
        db_event.resolved = True
        db.commit()
        db.refresh(db_event)
    return db_event


def create_recovery_plan(db: Session, plan: RecoveryPlanCreate) -> RecoveryPlan:
    """Create a new recovery plan for a setback."""
    db_plan = RecoveryPlan(
        setback_id=plan.setback_id,
        name=plan.name,
        goal=plan.goal,
        status="active",
        created_at=datetime.utcnow(),
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def list_recovery_plans(db: Session, skip: int = 0, limit: int = 100) -> list[RecoveryPlan]:
    """List all recovery plans."""
    return db.query(RecoveryPlan).offset(skip).limit(limit).all()


def get_recovery_plan(db: Session, plan_id: int) -> RecoveryPlan | None:
    """Get a specific recovery plan by ID."""
    return db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()


def update_recovery_plan_status(
    db: Session, plan_id: int, status: str
) -> RecoveryPlan | None:
    """Update recovery plan status (active, paused, completed)."""
    db_plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if db_plan:
        db_plan.status = status
        db.commit()
        db.refresh(db_plan)
    return db_plan


def add_recovery_action(db: Session, action: RecoveryActionCreate, plan_id: int) -> RecoveryAction:
    """Add a recovery action to a plan."""
    db_action = RecoveryAction(
        plan_id=plan_id,
        description=action.description,
        order=action.order,
        completed=False,
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


def complete_recovery_action(db: Session, action_id: int) -> RecoveryAction | None:
    """Mark a recovery action as completed."""
    db_action = db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
    if db_action:
        db_action.completed = True
        db_action.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_action)
    return db_action
