"""
PACK SG: Income Routing & Separation Engine
Service functions for income routing, rule management, and allocation
"""
from sqlalchemy.orm import Session
from app.models.income_routing import (
    IncomeRouteRule, IncomeEvent, IncomeRoutingLog, IncomeRoutingSummary
)
from datetime import datetime
from typing import List, Tuple, Optional


def create_route_rule(
    db: Session,
    rule_id: str,
    source: str,
    allocation_type: str,
    allocation_value: float,
    target_account: str,
    description: Optional[str] = None,
    notes: Optional[str] = None
) -> IncomeRouteRule:
    """Create a new income routing rule."""
    rule = IncomeRouteRule(
        rule_id=rule_id,
        source=source,
        description=description,
        allocation_type=allocation_type,
        allocation_value=allocation_value,
        target_account=target_account,
        notes=notes,
        active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_route_rule(db: Session, rule_id: int) -> Optional[IncomeRouteRule]:
    """Get a routing rule by ID."""
    return db.query(IncomeRouteRule).filter(IncomeRouteRule.id == rule_id).first()


def list_active_rules(db: Session, source: Optional[str] = None) -> List[IncomeRouteRule]:
    """List all active routing rules, optionally filtered by source."""
    query = db.query(IncomeRouteRule).filter(IncomeRouteRule.active == True)
    if source:
        query = query.filter(IncomeRouteRule.source == source)
    return query.all()


def update_rule_status(db: Session, rule_id: int, active: bool) -> IncomeRouteRule:
    """Enable or disable a routing rule."""
    rule = get_route_rule(db, rule_id)
    if rule:
        rule.active = active
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
    return rule


def log_income_event(
    db: Session,
    event_id: str,
    date: datetime,
    source: str,
    amount: int,
    notes: Optional[str] = None
) -> IncomeEvent:
    """Log an incoming income event."""
    event = IncomeEvent(
        event_id=event_id,
        date=date,
        source=source,
        amount=amount,
        notes=notes,
        routed=False
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_income_event(db: Session, event_id: str) -> Optional[IncomeEvent]:
    """Get an income event by event_id."""
    return db.query(IncomeEvent).filter(IncomeEvent.event_id == event_id).first()


def list_income_events(db: Session, source: Optional[str] = None, routed: Optional[bool] = None) -> List[IncomeEvent]:
    """List income events, optionally filtered."""
    query = db.query(IncomeEvent)
    if source:
        query = query.filter(IncomeEvent.source == source)
    if routed is not None:
        query = query.filter(IncomeEvent.routed == routed)
    return query.all()


def calculate_routing_allocation(
    db: Session,
    event_id: str,
    source: str
) -> List[Tuple[int, str, int, float]]:
    """
    Calculate routing allocations for an income event.
    Returns list of (rule_id, target_account, amount_cents, percent_of_total)
    """
    event = get_income_event(db, event_id)
    if not event:
        return []

    rules = list_active_rules(db, source)
    if not rules:
        return []

    allocations = []
    income_amount = event.amount

    for rule in rules:
        if rule.allocation_type == "percent":
            allocated = int(income_amount * (rule.allocation_value / 100))
        else:
            allocated = int(rule.allocation_value * 100)  # fixed is in dollars, convert to cents

        percent = (allocated / income_amount * 100) if income_amount > 0 else 0
        allocations.append((rule.id, rule.target_account, allocated, percent))

    return allocations


def create_routing_instruction(
    db: Session,
    log_id: str,
    rule_id: int,
    income_event_id: str,
    calculated_amount: int,
    target_account: str,
    notes: Optional[str] = None
) -> IncomeRoutingLog:
    """
    Create a routing instruction (log entry).
    Status starts as 'pending' awaiting user approval.
    """
    log = IncomeRoutingLog(
        log_id=log_id,
        rule_id=rule_id,
        income_event_id=income_event_id,
        calculated_amount=calculated_amount,
        target_account=target_account,
        status="pending",
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def approve_routing(db: Session, log_id: str) -> IncomeRoutingLog:
    """User approves a routing instruction."""
    log = db.query(IncomeRoutingLog).filter(IncomeRoutingLog.log_id == log_id).first()
    if log:
        log.status = "approved"
        log.user_approval_date = datetime.utcnow()
        db.commit()
        db.refresh(log)
    return log


def execute_routing(db: Session, log_id: str) -> IncomeRoutingLog:
    """Mark a routing as executed."""
    log = db.query(IncomeRoutingLog).filter(IncomeRoutingLog.log_id == log_id).first()
    if log and log.status == "approved":
        log.status = "executed"
        log.execution_date = datetime.utcnow()
        
        # Mark corresponding income event as routed
        event = db.query(IncomeEvent).filter(IncomeEvent.event_id == log.income_event_id).first()
        if event:
            event.routed = True
        
        db.commit()
        db.refresh(log)
    return log


def get_pending_routings(db: Session) -> List[IncomeRoutingLog]:
    """Get all pending routing instructions awaiting approval."""
    return db.query(IncomeRoutingLog).filter(IncomeRoutingLog.status == "pending").all()


def create_routing_summary(
    db: Session,
    summary_id: str,
    date: datetime,
    total_income: int,
    allocations: List[dict],
    unallocated_balance: int,
    notes: Optional[str] = None
) -> IncomeRoutingSummary:
    """Create a routing summary snapshot."""
    summary = IncomeRoutingSummary(
        summary_id=summary_id,
        date=date,
        total_income=total_income,
        allocations=allocations,
        unallocated_balance=unallocated_balance,
        notes=notes
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_routing_summary(db: Session, summary_id: str) -> Optional[IncomeRoutingSummary]:
    """Get a routing summary by ID."""
    return db.query(IncomeRoutingSummary).filter(IncomeRoutingSummary.summary_id == summary_id).first()


def get_routing_summaries_by_date_range(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> List[IncomeRoutingSummary]:
    """Get routing summaries within a date range."""
    return db.query(IncomeRoutingSummary).filter(
        IncomeRoutingSummary.date >= start_date,
        IncomeRoutingSummary.date <= end_date
    ).all()
