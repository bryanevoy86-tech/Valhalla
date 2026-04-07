"""
PACK AP: Decision Governance Router
Prefix: /governance/decisions
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.decision_governance import (
    DecisionPolicyCreate,
    DecisionPolicyUpdate,
    DecisionPolicyOut,
    DecisionCreate,
    DecisionUpdate,
    DecisionOut,
)
from app.services.decision_governance import (
    create_policy,
    update_policy,
    list_policies,
    get_policy_by_key,
    create_decision,
    update_decision,
    list_decisions_for_entity,
)

router = APIRouter(prefix="/governance/decisions", tags=["Governance"])


@router.post("/policies", response_model=DecisionPolicyOut)
def create_policy_endpoint(
    payload: DecisionPolicyCreate,
    db: Session = Depends(get_db),
):
    """Create a decision policy."""
    return create_policy(db, payload)


@router.get("/policies", response_model=List[DecisionPolicyOut])
def list_policies_endpoint(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List decision policies."""
    return list_policies(db, active_only=active_only)


@router.get("/policies/{key}", response_model=DecisionPolicyOut)
def get_policy_endpoint(
    key: str,
    db: Session = Depends(get_db),
):
    """Get a policy by key."""
    policy = get_policy_by_key(db, key)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/", response_model=DecisionOut)
def create_decision_endpoint(
    payload: DecisionCreate,
    db: Session = Depends(get_db),
):
    """Create a decision record."""
    return create_decision(db, payload)


@router.patch("/{decision_id}", response_model=DecisionOut)
def update_decision_endpoint(
    decision_id: int,
    payload: DecisionUpdate,
    db: Session = Depends(get_db),
):
    """Update a decision record."""
    obj = update_decision(db, decision_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Decision not found")
    return obj


@router.get("/by-entity", response_model=List[DecisionOut])
def list_decisions_for_entity_endpoint(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """List decisions for a specific entity."""
    return list_decisions_for_entity(db, entity_type, entity_id)
