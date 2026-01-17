"""PACK-CORE-PRELAUNCH-01: Safeguard Matrix - Router"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/safeguards", tags=["safeguards"])


@router.get("/", response_model=List[schemas.SafeguardRuleRead])
def list_safeguards(db: Session = Depends(get_db)):
    return service.list_rules(db)


@router.post("/", response_model=schemas.SafeguardRuleRead)
def create_safeguard(
    payload: schemas.SafeguardRuleCreate,
    db: Session = Depends(get_db),
):
    return service.create_rule(db, payload)


@router.patch("/{rule_id}", response_model=schemas.SafeguardRuleRead)
def update_safeguard(
    rule_id: UUID,
    payload: schemas.SafeguardRuleUpdate,
    db: Session = Depends(get_db),
):
    rule = service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return service.update_rule(db, rule, payload)
