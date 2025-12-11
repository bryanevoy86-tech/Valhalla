"""
PACK CI6: Trigger & Threshold Engine Service

NOTE:
Condition/action are generic JSON. Evaluation/execution will be done
by higher-level logic (e.g. Heimdall calling this service).
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.triggers import TriggerRule, TriggerEvent
from app.schemas.triggers import TriggerRuleIn


def upsert_trigger_rule(
    db: Session,
    payload: TriggerRuleIn,
) -> TriggerRule:
    """Create or update a trigger rule by name."""
    rule = (
        db.query(TriggerRule)
        .filter(TriggerRule.name == payload.name)
        .first()
    )
    if not rule:
        rule = TriggerRule(**payload.model_dump())
        db.add(rule)
    else:
        for field, value in payload.model_dump().items():
            setattr(rule, field, value)
        rule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(rule)
    return rule


def list_trigger_rules(
    db: Session,
) -> List[TriggerRule]:
    """List all trigger rules."""
    return (
        db.query(TriggerRule)
        .order_by(TriggerRule.created_at.asc())
        .all()
    )


def record_trigger_event(
    db: Session,
    rule_id: int,
    status: str,
    details: dict | None = None,
) -> TriggerEvent:
    """Record a trigger event."""
    evt = TriggerEvent(
        rule_id=rule_id,
        status=status,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt
