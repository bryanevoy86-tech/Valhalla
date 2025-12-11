from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.governance_decision import GovernanceDecision
from app.schemas.governance_decision import GovernanceDecisionIn


def record_decision(db: Session, payload: GovernanceDecisionIn) -> GovernanceDecision:
    """Record a governance decision (approval, denial, override, flag)."""
    obj = GovernanceDecision(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_decisions_for_subject(
    db: Session, subject_type: str, subject_id: int
) -> List[GovernanceDecision]:
    """Get all decisions for a specific subject (deal, contract, professional, etc.)."""
    return (
        db.query(GovernanceDecision)
        .filter(
            GovernanceDecision.subject_type == subject_type,
            GovernanceDecision.subject_id == subject_id,
        )
        .order_by(GovernanceDecision.created_at.asc())
        .all()
    )


def get_latest_final_decision(
    db: Session, subject_type: str, subject_id: int
) -> Optional[GovernanceDecision]:
    """Get the most recent final decision for a subject."""
    return (
        db.query(GovernanceDecision)
        .filter(
            GovernanceDecision.subject_type == subject_type,
            GovernanceDecision.subject_id == subject_id,
            GovernanceDecision.is_final == True,  # noqa: E712
        )
        .order_by(GovernanceDecision.created_at.desc())
        .first()
    )


def list_decisions_by_role(db: Session, role: str) -> List[GovernanceDecision]:
    """Get all decisions made by a specific role."""
    return (
        db.query(GovernanceDecision)
        .filter(GovernanceDecision.role == role)
        .order_by(GovernanceDecision.created_at.desc())
        .all()
    )


def get_decision_by_id(db: Session, decision_id: int) -> Optional[GovernanceDecision]:
    """Get a specific decision by ID."""
    return db.query(GovernanceDecision).filter(GovernanceDecision.id == decision_id).first()
