"""
PACK L0-09: Workflow Guardrails Service
Safety guardrails to prevent unsafe strategic decisions.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.workflow_guardrails import WorkflowGuardrail
from app.schemas.workflow_guardrails import WorkflowGuardrailCreate, WorkflowGuardrailUpdate


def create_guardrail(
    db: Session,
    tenant_id: str,
    payload: WorkflowGuardrailCreate,
) -> WorkflowGuardrail:
    """Create a new workflow guardrail."""
    guardrail = WorkflowGuardrail(
        tenant_id=tenant_id,
        **payload.model_dump()
    )
    db.add(guardrail)
    db.commit()
    db.refresh(guardrail)
    return guardrail


def list_guardrails(
    db: Session,
    tenant_id: str,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[WorkflowGuardrail], int]:
    """List workflow guardrails for a tenant."""
    query = db.query(WorkflowGuardrail).filter(WorkflowGuardrail.tenant_id == tenant_id)
    
    if active_only:
        query = query.filter(WorkflowGuardrail.active == True)
    
    total = query.count()
    items = query.order_by(WorkflowGuardrail.created_at).offset(skip).limit(limit).all()
    return items, total


def get_guardrail(db: Session, guardrail_id: int) -> Optional[WorkflowGuardrail]:
    """Get a specific workflow guardrail."""
    return db.query(WorkflowGuardrail).filter(WorkflowGuardrail.id == guardrail_id).first()


def update_guardrail(
    db: Session,
    guardrail_id: int,
    payload: WorkflowGuardrailUpdate,
) -> Optional[WorkflowGuardrail]:
    """Update a workflow guardrail."""
    guardrail = db.query(WorkflowGuardrail).filter(WorkflowGuardrail.id == guardrail_id).first()
    if not guardrail:
        return None
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(guardrail, field, value)
    
    db.commit()
    db.refresh(guardrail)
    return guardrail


def check_guardrails(
    db: Session,
    tenant_id: str,
    context: Dict[str, Any],
    applies_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check all active guardrails against a context.
    Returns ALLOW, WARN, or BLOCK decision.
    """
    guardrails, _ = list_guardrails(db, tenant_id, active_only=True)
    
    triggered = []
    auto_blocks = []
    
    for guardrail in guardrails:
        # Check if this guardrail applies
        if applies_to and guardrail.applies_to != "*" and guardrail.applies_to != applies_to:
            continue
        
        # Evaluate condition
        if _condition_matches(guardrail.condition, context):
            triggered.append({
                "guardrail_id": guardrail.id,
                "name": guardrail.name,
                "required_reviews": guardrail.required_reviews,
                "auto_block": guardrail.auto_block,
            })
            
            if guardrail.auto_block:
                auto_blocks.append(guardrail.id)
    
    # Determine overall decision
    if auto_blocks:
        decision = "BLOCK"
        message = f"Guardrails {auto_blocks} require review before proceeding"
    elif triggered:
        decision = "WARN"
        message = f"{len(triggered)} guardrail(s) require review"
    else:
        decision = "ALLOW"
        message = "All guardrails passed"
    
    return {
        "decision": decision,
        "message": message,
        "triggered_guardrails": triggered,
        "requires_reviews": sum(g["required_reviews"] for g in triggered),
    }


def _condition_matches(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Check if a condition matches the current context."""
    field = condition.get("field")
    operator = condition.get("operator", "gte")
    threshold = condition.get("value")
    
    if field not in context:
        return False
    
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
    elif operator == "in":
        return value in threshold if isinstance(threshold, list) else value == threshold
    
    return False


def delete_guardrail(db: Session, guardrail_id: int) -> bool:
    """Delete a workflow guardrail."""
    guardrail = db.query(WorkflowGuardrail).filter(WorkflowGuardrail.id == guardrail_id).first()
    if not guardrail:
        return False
    
    db.delete(guardrail)
    db.commit()
    return True
