"""
PACK L0-09: Tuning Rules Service
Decision thresholds and tuning rules for strategic decisions.
"""

from typing import Optional, List, Tuple, Dict, Any
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.tuning_rules import TuningRule
from app.schemas.tuning_rules import (
    ProfileConstraintSettings, ProfileSettings, TuningRuleCreate, TuningRuleUpdate,
)

PROFILE = "profile"
CONSTRAINT = "profile_constraint"


def _normalized_config(rule_type: str, config: dict) -> dict:
    schema = {PROFILE: ProfileSettings, CONSTRAINT: ProfileConstraintSettings}.get(rule_type)
    if schema is None:
        return config
    try:
        return schema.model_validate(config).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, "Invalid tuning profile or constraint configuration") from exc


def _tenant_rules(db: Session, tenant_id: str):
    return db.query(TuningRule).filter(TuningRule.tenant_id == tenant_id)


def _constraints(query, profile_id: int):
    return query.filter(
        TuningRule.rule_type == CONSTRAINT,
        TuningRule.config["profile_id"].as_integer() == profile_id,
    )


def create_rule(
    db: Session,
    tenant_id: str,
    payload: TuningRuleCreate,
) -> TuningRule:
    """Create a rule or atomically replace the settings of a named profile."""
    values = payload.model_dump()
    values["config"] = _normalized_config(payload.rule_type, payload.config)
    if payload.rule_type == PROFILE:
        insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
        statement = insert(TuningRule).values(tenant_id=tenant_id, **values)
        statement = statement.on_conflict_do_update(
            index_elements=[TuningRule.tenant_id, TuningRule.name],
            index_where=text("rule_type = 'profile'"),
            set_={
                "description": statement.excluded.description,
                "active": statement.excluded.active,
                "config": statement.excluded.config,
                "updated_at": statement.excluded.updated_at,
            },
        ).returning(TuningRule.id)
        rule_id = db.execute(statement).scalar_one()
        rule = _tenant_rules(db, tenant_id).filter_by(id=rule_id).one()
        db.refresh(rule)
        db.commit()
        return rule
    if payload.rule_type == CONSTRAINT:
        profile = _tenant_rules(db, tenant_id).filter_by(
            id=values["config"]["profile_id"], rule_type=PROFILE,
        ).with_for_update().first()
        if profile is None:
            raise HTTPException(404, "Profile not found")
    rule = TuningRule(tenant_id=tenant_id, **values)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_rules(
    db: Session,
    tenant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    rule_type: str | None = None,
    profile_id: int | None = None,
) -> Tuple[List[TuningRule], int]:
    """List tuning rules for a tenant."""
    query = _tenant_rules(db, tenant_id)
    if rule_type is not None:
        query = query.filter(TuningRule.rule_type == rule_type)
    if profile_id is not None:
        query = _constraints(query, profile_id)
    
    if active_only:
        query = query.filter(TuningRule.active == True)
    
    total = query.count()
    items = query.order_by(TuningRule.created_at, TuningRule.id).offset(skip).limit(limit).all()
    return items, total


def get_rule(db: Session, tenant_id: str, rule_id: int) -> Optional[TuningRule]:
    """Get a specific tuning rule."""
    return _tenant_rules(db, tenant_id).filter_by(id=rule_id).first()


def update_rule(
    db: Session,
    tenant_id: str,
    rule_id: int,
    payload: TuningRuleUpdate,
) -> Optional[TuningRule]:
    """Update a tuning rule."""
    rule = _tenant_rules(db, tenant_id).filter_by(id=rule_id).first()
    if not rule:
        return None
    
    updates = payload.model_dump(exclude_unset=True)
    if any(value is None and field != "description" for field, value in updates.items()):
        raise HTTPException(422, "Only description can be cleared")
    rule_type = updates.get("rule_type", rule.rule_type)
    metadata_types = {PROFILE, CONSTRAINT}
    if rule_type != rule.rule_type and metadata_types.intersection({rule_type, rule.rule_type}):
        raise HTTPException(409, "Tuning profile and constraint types cannot be changed")
    if rule_type == PROFILE and updates.get("name", rule.name) != rule.name:
        raise HTTPException(409, "Profile name is its identity")
    if "config" in updates:
        updates["config"] = _normalized_config(rule_type, updates["config"])
        if rule_type == CONSTRAINT and updates["config"]["profile_id"] != rule.config["profile_id"]:
            raise HTTPException(409, "Constraint cannot change profiles")
    for field, value in updates.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule


def evaluate_rules(
    db: Session,
    tenant_id: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate all active tuning rules against a context.
    Returns results and any violations found.
    """
    rules = _tenant_rules(db, tenant_id).filter(
        TuningRule.active.is_(True), TuningRule.rule_type.not_in((PROFILE, CONSTRAINT)),
    ).order_by(TuningRule.created_at, TuningRule.id).all()
    
    results = {
        "passed": [],
        "violations": [],
    }
    
    for rule in rules:
        rule_passed = _evaluate_single_rule(rule, context)
        if rule_passed:
            results["passed"].append({
                "rule_id": rule.id,
                "name": rule.name,
                "status": "PASS",
            })
        else:
            results["violations"].append({
                "rule_id": rule.id,
                "name": rule.name,
                "status": "FAIL",
                "rule_type": rule.rule_type,
                "config": rule.config,
            })
    
    return results


def _evaluate_single_rule(rule: TuningRule, context: Dict[str, Any]) -> bool:
    """Evaluate a single rule against context."""
    config = rule.config
    rule_type = rule.rule_type
    
    if rule_type == "threshold":
        # Check threshold conditions
        field = config.get("field")
        operator = config.get("operator", "gte")
        threshold = config.get("threshold")
        
        if field not in context:
            return True  # Field not in context, don't fail
        
        value = context[field]
        
        if operator == "gte":
            return value >= threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "gt":
            return value > threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "ne":
            return value != threshold
    
    elif rule_type == "toggle":
        # Boolean toggle rule
        expected = config.get("value", True)
        field = config.get("field")
        if field and field in context:
            return context[field] == expected
        return True
    
    elif rule_type == "percentage":
        # Percentage-based rule
        field = config.get("field")
        max_percent = config.get("max_percent", 100)
        if field in context:
            value = context[field]
            return value <= max_percent
        return True
    
    return True  # Unknown rule type, pass


def delete_rule(db: Session, tenant_id: str, rule_id: int) -> bool:
    """Delete a tuning rule."""
    query = _tenant_rules(db, tenant_id)
    rule = query.filter_by(id=rule_id).with_for_update().first()
    if not rule:
        return False
    if rule.rule_type == PROFILE and _constraints(query, rule_id).first() is not None:
        raise HTTPException(409, "Remove profile constraints before deleting the profile")
    
    db.delete(rule)
    db.commit()
    return True
