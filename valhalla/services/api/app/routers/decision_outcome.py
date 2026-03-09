"""
PACK CL9-10: Decision Outcome Router
Prefix: /heimdall/decisions
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.decision_outcome import (
    DecisionOutcomeCreate,
    DecisionOutcomeOut,
    DecisionOutcomeList,
)
from app.services.decision_outcome import (
    create_decision_outcome,
    list_decision_outcomes,
)

router = APIRouter(
    prefix="/heimdall/decisions",
    tags=["Heimdall", "Meta-Learning"],
)


@router.post("/outcomes", response_model=DecisionOutcomeOut, status_code=201)
def record_decision_outcome(
    payload: DecisionOutcomeCreate,
    db: Session = Depends(get_db),
):
    """
    Record the outcome of a decision Heimdall was involved in.

    This is the backbone of meta-learning and evolution: Heimdall can later
    analyze these records to see what works and what doesn't.
    """
    obj = create_decision_outcome(db, payload)
    return obj


@router.get("/outcomes", response_model=DecisionOutcomeList)
def get_decision_outcomes(
    domain: Optional[str] = Query(None),
    decision_id: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """
    List recorded decision outcomes, optionally filtered by domain or decision_id.
    """
    items = list_decision_outcomes(db, domain=domain, decision_id=decision_id, limit=limit)
    return DecisionOutcomeList(
        total=len(items),
        items=[DecisionOutcomeOut.model_validate(i) for i in items],
    )
