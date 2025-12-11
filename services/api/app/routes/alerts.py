"""PACK 73: Alerts & SLA Router
API endpoints for alert rules and events.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.alerts_service import (
    create_alert_rule,
    list_alert_rules,
    log_alert_event,
    list_alert_events,
)
from app.schemas.alerts import AlertRuleOut, AlertEventOut

router = APIRouter(prefix="/alerts", tags=["Alerts & SLA"])


@router.post("/rules", response_model=AlertRuleOut)
def new_alert_rule(
    name: str,
    condition_payload: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new alert rule."""
    return create_alert_rule(db, name, condition_payload, description)


@router.get("/rules", response_model=list[AlertRuleOut])
def get_alert_rules(active_only: bool = False, db: Session = Depends(get_db)):
    """Get alert rules, optionally filtered to active only."""
    return list_alert_rules(db, active_only)


@router.post("/events", response_model=AlertEventOut)
def new_alert_event(
    level: str,
    message: str,
    rule_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Log a new alert event."""
    return log_alert_event(db, level, message, rule_id)


@router.get("/events", response_model=list[AlertEventOut])
def get_alert_events(level: Optional[str] = None, db: Session = Depends(get_db)):
    """Get alert events, optionally filtered by level."""
    return list_alert_events(db, level)
