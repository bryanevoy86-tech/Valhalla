"""
PACK SG: Income Routing & Separation Engine
FastAPI router for income routing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.income_routing import (
    IncomeRouteRuleSchema, IncomeEventSchema, IncomeRoutingLogSchema,
    IncomeRoutingSummarySchema, RoutingResponseSchema, AllocationDetail
)
from app.services import income_routing
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/income", tags=["PACK SG: Income Routing"])


@router.post("/rules", response_model=IncomeRouteRuleSchema)
def create_routing_rule(
    rule_data: IncomeRouteRuleSchema,
    db: Session = Depends(get_db)
):
    """Create a new income routing rule."""
    rule = income_routing.create_route_rule(
        db,
        rule_id=rule_data.rule_id,
        source=rule_data.source,
        allocation_type=rule_data.allocation_type,
        allocation_value=rule_data.allocation_value,
        target_account=rule_data.target_account,
        description=rule_data.description,
        notes=rule_data.notes
    )
    return rule


@router.get("/rules", response_model=list[IncomeRouteRuleSchema])
def get_active_rules(source: str = None, db: Session = Depends(get_db)):
    """Get all active routing rules, optionally filtered by source."""
    rules = income_routing.list_active_rules(db, source)
    return rules


@router.patch("/rules/{rule_id}/status")
def toggle_rule_status(rule_id: int, active: bool, db: Session = Depends(get_db)):
    """Enable or disable a routing rule."""
    rule = income_routing.update_rule_status(db, rule_id, active)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "updated", "rule_id": rule.rule_id, "active": active}


@router.post("/events", response_model=IncomeEventSchema)
def log_income(
    event_data: IncomeEventSchema,
    db: Session = Depends(get_db)
):
    """Log an incoming income event."""
    event = income_routing.log_income_event(
        db,
        event_id=event_data.event_id,
        date=event_data.date,
        source=event_data.source,
        amount=event_data.amount,
        notes=event_data.notes
    )
    return event


@router.get("/events", response_model=list[IncomeEventSchema])
def list_events(source: str = None, routed: bool = None, db: Session = Depends(get_db)):
    """List income events, optionally filtered by source or routed status."""
    events = income_routing.list_income_events(db, source, routed)
    return events


@router.post("/calculate/{event_id}")
def calculate_routing(event_id: str, db: Session = Depends(get_db)):
    """
    Calculate routing allocations for an income event.
    Returns proposed routing plan without executing it.
    """
    event = income_routing.get_income_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    allocations = income_routing.calculate_routing_allocation(db, event_id, event.source)
    
    total_allocated = sum(amount for _, _, amount, _ in allocations)
    unallocated = event.amount - total_allocated

    response = {
        "event_id": event_id,
        "total_income": event.amount,
        "proposed_allocations": [
            {
                "target_account": target,
                "amount": amount,
                "percent_of_total": percent
            } for _, target, amount, percent in allocations
        ],
        "unallocated_balance": unallocated
    }
    return response


@router.post("/routing/approve/{log_id}")
def approve_routing_instruction(log_id: str, db: Session = Depends(get_db)):
    """User approves a routing instruction."""
    log = income_routing.approve_routing(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Routing instruction not found")
    return {"log_id": log_id, "status": log.status, "approval_date": log.user_approval_date}


@router.post("/routing/execute/{log_id}")
def execute_routing_instruction(log_id: str, db: Session = Depends(get_db)):
    """Execute an approved routing instruction."""
    log = income_routing.execute_routing(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Routing instruction not found")
    return {"log_id": log_id, "status": log.status, "execution_date": log.execution_date}


@router.get("/pending-routings")
def get_pending(db: Session = Depends(get_db)):
    """Get all pending routing instructions awaiting user approval."""
    logs = income_routing.get_pending_routings(db)
    return [
        {
            "log_id": log.log_id,
            "income_event_id": log.income_event_id,
            "calculated_amount": log.calculated_amount,
            "target_account": log.target_account,
            "status": log.status
        } for log in logs
    ]


@router.post("/summaries", response_model=IncomeRoutingSummarySchema)
def create_summary(
    summary_data: IncomeRoutingSummarySchema,
    db: Session = Depends(get_db)
):
    """Create a routing summary snapshot."""
    summary = income_routing.create_routing_summary(
        db,
        summary_id=summary_data.summary_id,
        date=summary_data.date,
        total_income=summary_data.total_income,
        allocations=[dict(a) for a in summary_data.allocations],
        unallocated_balance=summary_data.unallocated_balance,
        notes=summary_data.notes
    )
    return summary


@router.get("/summaries/{summary_id}", response_model=IncomeRoutingSummarySchema)
def get_summary(summary_id: str, db: Session = Depends(get_db)):
    """Get a routing summary by ID."""
    summary = income_routing.get_routing_summary(db, summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary
