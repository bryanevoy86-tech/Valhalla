"""
PACK CI6: Trigger & Threshold Engine Router
Prefix: /intelligence/triggers
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.triggers import TriggerEvent
from app.schemas.triggers import (
    TriggerRuleIn,
    TriggerRuleOut,
    TriggerRuleList,
    TriggerEventOut,
    TriggerEventList,
    TriggerEvaluationRequest,
)
from app.services.triggers import (
    upsert_trigger_rule,
    list_trigger_rules,
    record_trigger_event,
)

router = APIRouter(prefix="/intelligence/triggers", tags=["Intelligence", "Triggers"])


@router.post("/rules", response_model=TriggerRuleOut)
def upsert_rule_endpoint(
    payload: TriggerRuleIn,
    db: Session = Depends(get_db),
):
    """Create or update a trigger rule."""
    return upsert_trigger_rule(db, payload)


@router.get("/rules", response_model=TriggerRuleList)
def list_rules_endpoint(
    db: Session = Depends(get_db),
):
    """List all trigger rules."""
    items = list_trigger_rules(db)
    return TriggerRuleList(total=len(items), items=items)


@router.post("/evaluate", response_model=TriggerEventOut)
def evaluate_trigger_endpoint(
    payload: TriggerEvaluationRequest,
    db: Session = Depends(get_db),
):
    """
    Record a trigger evaluation/fire event.
    The actual condition checking and action execution is done
    by Heimdall or another service that understands `condition` and `action`.
    """
    evt = record_trigger_event(
        db,
        rule_id=payload.rule_id,
        status="fired",
        details={"context": payload.context},
    )
    return TriggerEventOut.model_validate(evt)


@router.get("/events", response_model=TriggerEventList)
def list_events_endpoint(
    db: Session = Depends(get_db),
):
    """List recent trigger events."""
    items = (
        db.query(TriggerEvent)
        .order_by(TriggerEvent.created_at.desc())
        .limit(500)
        .all()
    )
    return TriggerEventList(
        total=len(items),
        items=[TriggerEventOut.model_validate(i) for i in items],
    )
