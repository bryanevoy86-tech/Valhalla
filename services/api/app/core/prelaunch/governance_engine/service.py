"""Governance Engine Service Layer"""
from sqlalchemy.orm import Session
from . import models, schemas


def list_rules(db: Session):
    """List all policy rules, ordered by code."""
    return db.query(models.PolicyRule).order_by(models.PolicyRule.code).all()


def get_rule(db: Session, rule_id):
    """Get a specific policy rule by ID."""
    return db.query(models.PolicyRule).filter(models.PolicyRule.id == rule_id).first()


def create_rule(db: Session, data: schemas.PolicyRuleCreate):
    """Create a new policy rule."""
    r = models.PolicyRule(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_rule(db: Session, rule: models.PolicyRule, data: schemas.PolicyRuleUpdate):
    """Update an existing policy rule."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule
