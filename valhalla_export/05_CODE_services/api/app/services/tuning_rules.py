"""
PACK L0-09: Tuning Rules Service
Decision thresholds and tuning rules for strategic decisions.
"""

from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.tuning_rules import TuningRule
from app.schemas.tuning_rules import TuningRuleCreate, TuningRuleUpdate


def create_rule(
    db: Session,
    tenant_id: str,
    payload: TuningRuleCreate,
) -> TuningRule:
    """Create a new tuning rule."""
    rule = TuningRule(
        tenant_id=tenant_id,
        **payload.model_dump()
    )
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
) -> Tuple[List[TuningRule], int]:
    """List tuning rules for a tenant."""
    query = db.query(TuningRule).filter(TuningRule.tenant_id == tenant_id)
    
    if active_only:
        query = query.filter(TuningRule.active == True)
    
    total = query.count()
    items = query.order_by(TuningRule.created_at).offset(skip).limit(limit).all()
    return items, total


def get_rule(db: Session, rule_id: int) -> Optional[TuningRule]:
    """Get a specific tuning rule."""
    return db.query(TuningRule).filter(TuningRule.id == rule_id).first()


def update_rule(
    db: Session,
    rule_id: int,
    payload: TuningRuleUpdate,
) -> Optional[TuningRule]:
    """Update a tuning rule."""
    rule = db.query(TuningRule).filter(TuningRule.id == rule_id).first()
    if not rule:
        return None
    
    for field, value in payload.model_dump(exclude_unset=True).items():
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
    rules, _ = list_rules(db, tenant_id, active_only=True)
    
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


def delete_rule(db: Session, rule_id: int) -> bool:
    """Delete a tuning rule."""
    rule = db.query(TuningRule).filter(TuningRule.id == rule_id).first()
    if not rule:
        return False
    
    db.delete(rule)
    db.commit()
    return True
    """List all constraints for a profile."""
    return (
        db.query(TuningConstraint)
        .filter(TuningConstraint.profile_id == profile_id)
        .order_by(TuningConstraint.created_at.asc())
        .all()
    )
