"""
PACK L0-09: Strategic Decision Router
Proposes and manages strategic decisions with approval workflow.
Prefix: /api/v1/strategic/decisions
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.strategic_decision import (
    StrategicDecisionCreate,
    StrategicDecisionStatusUpdate,
    StrategicDecisionOut,
    StrategicDecisionList,
)
from app.services import strategic_decision as service

router = APIRouter(
    prefix="/api/v1/strategic/decisions",
    tags=["Strategic Engine", "Decisions"],
)


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    return "default-tenant"


def get_user_id(request) -> str:
    """Extract user_id from request context."""
    return "default-user"


@router.post("", response_model=StrategicDecisionOut, status_code=201)
def propose_decision(
    payload: StrategicDecisionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Propose a new strategic decision."""
    return service.propose_decision(db, tenant_id, payload)


@router.get("", response_model=StrategicDecisionList)
def list_decisions_endpoint(
    status: Optional[str] = Query(None, description="Filter by decision status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List strategic decisions for the tenant."""
    items, total = service.list_decisions(
        db,
        tenant_id=tenant_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return StrategicDecisionList(total=total, items=items)


@router.get("/{decision_id}", response_model=StrategicDecisionOut)
def get_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific decision."""
    decision = service.get_decision(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.patch("/{decision_id}/status", response_model=StrategicDecisionOut)
def update_decision_status(
    decision_id: int,
    payload: StrategicDecisionStatusUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Update decision status in workflow."""
    decision = service.update_decision_status(db, decision_id, payload)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{decision_id}/approve", response_model=StrategicDecisionOut)
def approve_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Approve a decision."""
    decision = service.approve_decision(db, decision_id, user_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{decision_id}/reject", response_model=StrategicDecisionOut)
def reject_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Reject a decision."""
    decision = service.reject_decision(db, decision_id, user_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{decision_id}/execute", response_model=StrategicDecisionOut)
def execute_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    """Execute a decision."""
    decision = service.execute_decision(db, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.delete("/{decision_id}", status_code=204)
def delete_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    """Delete a decision."""
    success = service.delete_decision(db, decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found")
    return None
