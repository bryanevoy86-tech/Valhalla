"""
PACK L0-09: Tuning Rules Router
Decision thresholds and tuning rules.
Prefix: /api/v1/tuning/rules
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.tuning_rules import (
    TuningRuleCreate,
    TuningRuleUpdate,
    TuningRuleOut,
    TuningRuleList,
)
from app.services import tuning_rules as service

router = APIRouter(
    prefix="/api/v1/tuning/rules",
    tags=["Strategic Engine", "Tuning"],
)


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    return "default-tenant"


@router.post("", response_model=TuningRuleOut, status_code=201)
def create_rule(
    payload: TuningRuleCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new tuning rule."""
    return service.create_rule(db, tenant_id, payload)


@router.get("", response_model=TuningRuleList)
def list_rules(
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List tuning rules for the tenant."""
    items, total = service.list_rules(db, tenant_id, active_only=active_only, skip=skip, limit=limit)
    return TuningRuleList(total=total, items=items)


@router.get("/{rule_id}", response_model=TuningRuleOut)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific tuning rule."""
    rule = service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=TuningRuleOut)
def update_rule(
    rule_id: int,
    payload: TuningRuleUpdate,
    db: Session = Depends(get_db),
):
    """Update a tuning rule."""
    rule = service.update_rule(db, rule_id, payload)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/evaluate", response_model=dict)
def evaluate_rules(
    context: dict,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Evaluate all active tuning rules against a context."""
    return service.evaluate_rules(db, tenant_id, context)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """Delete a tuning rule."""
    success = service.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return None
    add_constraint,
    list_constraints_for_profile,
)

router = APIRouter(prefix="/intelligence/tuning", tags=["Intelligence", "Tuning"])


@router.post("/profiles", response_model=TuningProfileOut)
def upsert_profile_endpoint(
    payload: TuningProfileIn,
    db: Session = Depends(get_db),
):
    """Create or update a tuning profile."""
    return upsert_profile(db, payload)


@router.get("/profiles", response_model=TuningProfileList)
def list_profiles_endpoint(
    db: Session = Depends(get_db),
):
    """List all tuning profiles."""
    items = list_profiles(db)
    return TuningProfileList(total=len(items), items=items)


@router.post("/constraints", response_model=TuningConstraintOut)
def add_constraint_endpoint(
    payload: TuningConstraintIn,
    db: Session = Depends(get_db),
):
    """Add a constraint to a profile."""
    return add_constraint(db, payload)


@router.get("/profiles/{profile_id}/constraints", response_model=TuningConstraintList)
def list_constraints_endpoint(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """List all constraints for a profile."""
    items = list_constraints_for_profile(db, profile_id=profile_id)
    return TuningConstraintList(total=len(items), items=items)
