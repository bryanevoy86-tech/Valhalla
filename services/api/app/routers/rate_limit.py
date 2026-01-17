"""
PACK UC: Rate Limiting & Quota Engine Router
Prefix: /system/ratelimits
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.rate_limit import (
    RateLimitRuleSet,
    RateLimitRuleOut,
    RateLimitRuleList,
    RateLimitSnapshotOut,
)
from app.services.rate_limit import (
    set_rate_limit_rule,
    list_rate_limit_rules,
    get_rate_limit_rule,
    delete_rate_limit_rule,
    get_snapshots,
)

router = APIRouter(prefix="/system/ratelimits", tags=["Rate Limits"])


@router.post("/rules", response_model=RateLimitRuleOut)
def set_rule_endpoint(
    payload: RateLimitRuleSet,
    db: Session = Depends(get_db),
):
    return set_rate_limit_rule(db, payload)


@router.get("/rules", response_model=RateLimitRuleList)
def list_rules_endpoint(
    scope: str | None = Query(None),
    db: Session = Depends(get_db),
):
    items = list_rate_limit_rules(db, scope=scope)
    return RateLimitRuleList(total=len(items), items=items)


@router.get("/rules/{rule_id}", response_model=RateLimitRuleOut)
def get_rule_endpoint(
    rule_id: int,
    db: Session = Depends(get_db),
):
    obj = get_rate_limit_rule(db, rule_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Rate limit rule not found")
    return obj


@router.delete("/rules/{rule_id}")
def delete_rule_endpoint(
    rule_id: int,
    db: Session = Depends(get_db),
):
    ok = delete_rate_limit_rule(db, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rate limit rule not found")
    return {"deleted": True}


@router.get("/snapshots", response_model=List[RateLimitSnapshotOut])
def list_snapshots_endpoint(
    scope: str | None = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    return get_snapshots(db, scope=scope, limit=limit)
