"""
PACK UC: Rate Limiting & Quota Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.rate_limit import RateLimitRule, RateLimitSnapshot
from app.schemas.rate_limit import RateLimitRuleSet


def set_rate_limit_rule(
    db: Session,
    payload: RateLimitRuleSet,
) -> RateLimitRule:
    obj = (
        db.query(RateLimitRule)
        .filter(
            RateLimitRule.scope == payload.scope,
            RateLimitRule.key == payload.key,
        )
        .first()
    )
    if not obj:
        obj = RateLimitRule(**payload.model_dump())
        db.add(obj)
    else:
        obj.window_seconds = payload.window_seconds
        obj.max_requests = payload.max_requests
        obj.enabled = payload.enabled
        obj.description = payload.description
        obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(obj)
    return obj


def list_rate_limit_rules(
    db: Session,
    scope: Optional[str] = None,
) -> List[RateLimitRule]:
    q = db.query(RateLimitRule)
    if scope:
        q = q.filter(RateLimitRule.scope == scope)
    return q.order_by(RateLimitRule.created_at.desc()).all()


def get_rate_limit_rule(
    db: Session,
    rule_id: int,
) -> Optional[RateLimitRule]:
    return db.query(RateLimitRule).filter(RateLimitRule.id == rule_id).first()


def delete_rate_limit_rule(
    db: Session,
    rule_id: int,
) -> bool:
    obj = get_rate_limit_rule(db, rule_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_snapshots(
    db: Session,
    scope: Optional[str] = None,
    limit: int = 200,
) -> List[RateLimitSnapshot]:
    q = db.query(RateLimitSnapshot)
    if scope:
        q = q.filter(RateLimitSnapshot.scope == scope)
    return (
        q.order_by(RateLimitSnapshot.updated_at.desc())
        .limit(limit)
        .all()
    )
