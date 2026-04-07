"""Governance Engine Router - Policy & Decision Guardrails"""
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service, models

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/policies", response_model=List[schemas.PolicyRuleRead])
def get_policies(db: Session = Depends(get_db)):
    """List all active policy rules."""
    return [schemas.PolicyRuleRead.model_validate(r) for r in service.list_rules(db)]


@router.post("/policies", response_model=schemas.PolicyRuleRead)
def add_policy(payload: schemas.PolicyRuleCreate, db: Session = Depends(get_db)):
    """Add a new policy rule."""
    r = service.create_rule(db, payload)
    return schemas.PolicyRuleRead.model_validate(r)


@router.patch("/policies/{rule_id}", response_model=schemas.PolicyRuleRead)
def modify_policy(
    rule_id: UUID,
    payload: schemas.PolicyRuleUpdate,
    db: Session = Depends(get_db),
):
    """Modify an existing policy rule."""
    r = service.get_rule(db, rule_id)
    if not r:
        raise HTTPException(status_code=404, detail="Policy not found")

    updated = service.update_rule(db, r, payload)
    return schemas.PolicyRuleRead.model_validate(updated)
