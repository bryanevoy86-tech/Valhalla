"""PACK 73: Alerts & SLA Service
Service layer for alert rules and events.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.alerts import AlertRule, AlertEvent


def create_alert_rule(
    db: Session,
    name: str,
    condition_payload: str,
    description: Optional[str] = None,
) -> AlertRule:
    """Create a new alert rule."""
    rule = AlertRule(
        name=name,
        description=description,
        condition_payload=condition_payload,
        active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_alert_rules(db: Session, active_only: bool = False) -> list:
    """List alert rules, optionally filtered to active only."""
    q = db.query(AlertRule)
    if active_only:
        q = q.filter(AlertRule.active == True)
    return q.order_by(AlertRule.id.desc()).all()


def log_alert_event(
    db: Session,
    level: str,
    message: str,
    rule_id: Optional[int] = None,
) -> AlertEvent:
    """Log an alert event."""
    ev = AlertEvent(
        rule_id=rule_id,
        level=level,
        message=message,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_alert_events(db: Session, level: Optional[str] = None) -> list:
    """List alert events, optionally filtered by level."""
    q = db.query(AlertEvent)
    if level is not None:
        q = q.filter(AlertEvent.level == level)
    return q.order_by(AlertEvent.id.desc()).all()
