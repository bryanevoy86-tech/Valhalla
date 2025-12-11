"""
PACK L0-09: Strategic Decision Service
Proposes and manages strategic decisions with evaluation and approval workflow.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.strategic_decision import StrategicDecision
from app.schemas.strategic_decision import (
    StrategicDecisionCreate,
    StrategicDecisionStatusUpdate,
)


def propose_decision(
    db: Session,
    tenant_id: str,
    payload: StrategicDecisionCreate,
) -> StrategicDecision:
    """Propose a new strategic decision."""
    decision = StrategicDecision(
        tenant_id=tenant_id,
        timestamp=datetime.utcnow(),
        status="PENDING",
        **payload.model_dump()
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def list_decisions(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[StrategicDecision], int]:
    """List strategic decisions for a tenant."""
    query = db.query(StrategicDecision).filter(StrategicDecision.tenant_id == tenant_id)
    
    if status:
        query = query.filter(StrategicDecision.status == status)
    
    total = query.count()
    items = query.order_by(StrategicDecision.timestamp.desc()).offset(skip).limit(limit).all()
    return items, total


def get_decision(db: Session, decision_id: int) -> Optional[StrategicDecision]:
    """Get a specific decision."""
    return db.query(StrategicDecision).filter(StrategicDecision.id == decision_id).first()


def update_decision_status(
    db: Session,
    decision_id: int,
    payload: StrategicDecisionStatusUpdate,
) -> Optional[StrategicDecision]:
    """Update decision status in workflow."""
    decision = db.query(StrategicDecision).filter(StrategicDecision.id == decision_id).first()
    if not decision:
        return None
    
    decision.status = payload.status
    decision.reviewer = payload.reviewer
    decision.reviewed_at = datetime.utcnow()
    
    if payload.status == "EXECUTED":
        decision.executed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(decision)
    return decision


def approve_decision(
    db: Session,
    decision_id: int,
    reviewer: str,
) -> Optional[StrategicDecision]:
    """Approve a decision."""
    return update_decision_status(
        db,
        decision_id,
        StrategicDecisionStatusUpdate(status="APPROVED", reviewer=reviewer)
    )


def reject_decision(
    db: Session,
    decision_id: int,
    reviewer: str,
) -> Optional[StrategicDecision]:
    """Reject a decision."""
    return update_decision_status(
        db,
        decision_id,
        StrategicDecisionStatusUpdate(status="REJECTED", reviewer=reviewer)
    )


def execute_decision(
    db: Session,
    decision_id: int,
) -> Optional[StrategicDecision]:
    """Mark a decision as executed."""
    decision = db.query(StrategicDecision).filter(StrategicDecision.id == decision_id).first()
    if not decision:
        return None
    
    decision.status = "EXECUTED"
    decision.executed_at = datetime.utcnow()
    db.commit()
    db.refresh(decision)
    return decision


def list_decisions_by_mode(
    db: Session,
    mode_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[StrategicDecision], int]:
    """List decisions made under a specific mode."""
    query = db.query(StrategicDecision).filter(StrategicDecision.mode_id == mode_id)
    total = query.count()
    items = query.order_by(StrategicDecision.timestamp.desc()).offset(skip).limit(limit).all()
    return items, total


def delete_decision(db: Session, decision_id: int) -> bool:
    """Delete a decision."""
    decision = db.query(StrategicDecision).filter(StrategicDecision.id == decision_id).first()
    if not decision:
        return False
    
    db.delete(decision)
    db.commit()
    return True
    db.commit()
    db.refresh(obj)
    return obj
