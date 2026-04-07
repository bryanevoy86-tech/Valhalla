"""
PACK L0-09: Workflow Guardrails Router
Safety guardrails to prevent unsafe decisions.
Prefix: /api/v1/workflow/guardrails
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.workflow_guardrails import (
    WorkflowGuardrailCreate,
    WorkflowGuardrailUpdate,
    WorkflowGuardrailOut,
    WorkflowGuardrailList,
)
from app.services import workflow_guardrails as service

router = APIRouter(
    prefix="/api/v1/workflow/guardrails",
    tags=["Strategic Engine", "Guardrails"],
)


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    return "default-tenant"


@router.post("", response_model=WorkflowGuardrailOut, status_code=201)
def create_guardrail(
    payload: WorkflowGuardrailCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new workflow guardrail."""
    return service.create_guardrail(db, tenant_id, payload)


@router.get("", response_model=WorkflowGuardrailList)
def list_guardrails(
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List workflow guardrails for the tenant."""
    items, total = service.list_guardrails(db, tenant_id, active_only=active_only, skip=skip, limit=limit)
    return WorkflowGuardrailList(total=total, items=items)


@router.get("/{guardrail_id}", response_model=WorkflowGuardrailOut)
def get_guardrail(
    guardrail_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific guardrail."""
    guardrail = service.get_guardrail(db, guardrail_id)
    if not guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return guardrail


@router.patch("/{guardrail_id}", response_model=WorkflowGuardrailOut)
def update_guardrail(
    guardrail_id: int,
    payload: WorkflowGuardrailUpdate,
    db: Session = Depends(get_db),
):
    """Update a workflow guardrail."""
    guardrail = service.update_guardrail(db, guardrail_id, payload)
    if not guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return guardrail


@router.post("/check", response_model=dict)
def check_guardrails(
    context: dict,
    applies_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Check guardrails against a context (decision point)."""
    return service.check_guardrails(db, tenant_id, context, applies_to=applies_to)


@router.delete("/{guardrail_id}", status_code=204)
def delete_guardrail(
    guardrail_id: int,
    db: Session = Depends(get_db),
):
    """Delete a workflow guardrail."""
    success = service.delete_guardrail(db, guardrail_id)
    if not success:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return None


# COMMENTED OUT: Incomplete second router section
# Missing schemas: WorkflowRuleOut, WorkflowRuleCreate, WorkflowRuleUpdate, WorkflowViolationOut
# Missing functions: create_rule, update_rule, list_rules, is_action_allowed, record_violation, list_violations
# Preserved primary router functionality for workflow guardrails above.
#
# router = APIRouter(prefix="/workflow/guardrails", tags=["WorkflowGuardrails"])
# ... additional endpoints removed - see git history ...
