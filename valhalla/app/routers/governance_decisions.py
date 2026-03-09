from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.governance_decision import (
    GovernanceDecisionIn,
    GovernanceDecisionOut,
)
from app.services.governance_service import (
    record_decision,
    list_decisions_for_subject,
    get_latest_final_decision,
    list_decisions_by_role,
    get_decision_by_id,
)

router = APIRouter(prefix="/governance/decisions", tags=["Governance", "Decisions"])


@router.post("/", response_model=GovernanceDecisionOut, status_code=status.HTTP_201_CREATED)
def create_decision(
    payload: GovernanceDecisionIn,
    db: Session = Depends(get_db),
):
    """Record a governance decision (approval, denial, override, flag)."""
    return record_decision(db, payload)


@router.get("/{decision_id}", response_model=GovernanceDecisionOut)
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    """Get a specific governance decision by ID."""
    return get_decision_by_id(db, decision_id)


@router.get(
    "/subject/{subject_type}/{subject_id}",
    response_model=List[GovernanceDecisionOut],
)
def get_subject_decisions(
    subject_type: str,
    subject_id: int,
    db: Session = Depends(get_db),
):
    """Get all decisions for a specific subject (deal, contract, professional, etc.)."""
    return list_decisions_for_subject(db, subject_type, subject_id)


@router.get(
    "/subject/{subject_type}/{subject_id}/latest-final",
    response_model=Optional[GovernanceDecisionOut],
)
def get_subject_latest_final(
    subject_type: str,
    subject_id: int,
    db: Session = Depends(get_db),
):
    """Get the most recent final decision for a subject."""
    return get_latest_final_decision(db, subject_type, subject_id)


@router.get("/by-role/{role}", response_model=List[GovernanceDecisionOut])
def get_decisions_by_role(role: str, db: Session = Depends(get_db)):
    """Get all decisions made by a specific role."""
    return list_decisions_by_role(db, role)
