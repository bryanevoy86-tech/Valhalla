"""
PACK TL: Strategic Decision Archive Router
Prefix: /decisions
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.strategic_decision import (
    StrategicDecisionCreate,
    StrategicDecisionOut,
    DecisionRevisionCreate,
    DecisionRevisionOut,
)
from app.services.strategic_decision import (
    create_decision,
    list_decisions,
    add_revision,
    update_decision_status,
)

router = APIRouter(prefix="/decisions", tags=["Strategic Decisions"])


@router.post("/", response_model=StrategicDecisionOut)
def create_decision_endpoint(
    payload: StrategicDecisionCreate,
    db: Session = Depends(get_db),
):
    """Create a new strategic decision."""
    return create_decision(db, payload)


@router.get("/", response_model=List[StrategicDecisionOut])
def list_decisions_endpoint(
    db: Session = Depends(get_db),
):
    """List all strategic decisions."""
    return list_decisions(db)


@router.post("/revisions", response_model=DecisionRevisionOut)
def add_revision_endpoint(
    payload: DecisionRevisionCreate,
    db: Session = Depends(get_db),
):
    """Add a revision to a strategic decision."""
    rev = add_revision(db, payload)
    if not rev:
        raise HTTPException(status_code=404, detail="Decision not found")
    return rev


@router.post("/{decision_id}/status/{status}", response_model=StrategicDecisionOut)
def update_decision_status_endpoint(
    decision_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    """Update the status of a strategic decision."""
    obj = update_decision_status(db, decision_id, status)
    if not obj:
        raise HTTPException(status_code=404, detail="Decision not found")
    return obj
