from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.freeze.schemas import (
    FreezeRuleCreate,
    FreezeRuleResponse,
    FreezeEventResponse,
)
from app.freeze.service import (
    create_rule,
    list_rules,
    evaluate_metric,
    list_events,
    resolve_event,
)


router = APIRouter(prefix="/freeze", tags=["freeze"])


@router.post("/rules", response_model=FreezeRuleResponse)
def add_rule(rule: FreezeRuleCreate, db: Session = Depends(get_db)):
    return create_rule(db, rule)


@router.get("/rules", response_model=List[FreezeRuleResponse])
def get_rules(db: Session = Depends(get_db)):
    return list_rules(db)


@router.post("/evaluate", response_model=Optional[FreezeEventResponse])
def eval_metric(metric: str, value: float, db: Session = Depends(get_db)):
    return evaluate_metric(db, metric, value)


@router.get("/events", response_model=List[FreezeEventResponse])
def get_events(unresolved_only: bool = False, db: Session = Depends(get_db)):
    return list_events(db, unresolved_only)


@router.post("/events/{event_id}/resolve", response_model=FreezeEventResponse)
def resolve(event_id: int, db: Session = Depends(get_db)):
    evt = resolve_event(db, event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt
