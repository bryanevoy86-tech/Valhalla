"""PACK-CORE-PRELAUNCH-01: Safeguard Matrix - Service"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def list_rules(db: Session) -> List[models.SafeguardRule]:
    return db.query(models.SafeguardRule).order_by(models.SafeguardRule.name).all()


def get_rule(db: Session, rule_id: UUID) -> Optional[models.SafeguardRule]:
    return db.query(models.SafeguardRule).filter(models.SafeguardRule.id == rule_id).first()


def create_rule(db: Session, data: schemas.SafeguardRuleCreate) -> models.SafeguardRule:
    rule = models.SafeguardRule(**data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(
    db: Session, rule: models.SafeguardRule, data: schemas.SafeguardRuleUpdate
) -> models.SafeguardRule:
    for field, value in data.dict(exclude_unset=True).items():
        setattr(rule, field, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
