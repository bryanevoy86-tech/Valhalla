"""
PACK L0-09: Workflow Guardrails Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class WorkflowGuardrailBase(BaseModel):
    """Base schema for workflow guardrails."""
    name: str = Field(..., description="Guardrail name")
    description: Optional[str] = None
    applies_to: str = Field(default="*", description="Module/route this applies to")
    condition: Dict[str, Any] = Field(..., description="Trigger condition")
    required_reviews: int = Field(default=1, ge=1, description="Number of reviews required")
    auto_block: bool = Field(default=False, description="Block vs warn")
    active: bool = Field(default=True)


class WorkflowGuardrailCreate(WorkflowGuardrailBase):
    """Schema for creating a workflow guardrail."""
    pass


class WorkflowGuardrailUpdate(BaseModel):
    """Schema for updating a workflow guardrail."""
    name: Optional[str] = None
    description: Optional[str] = None
    applies_to: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    required_reviews: Optional[int] = None
    auto_block: Optional[bool] = None
    active: Optional[bool] = None


class WorkflowGuardrailOut(WorkflowGuardrailBase):
    """Schema for outputting a workflow guardrail."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowGuardrailList(BaseModel):
    """Paginated list of workflow guardrails."""
    total: int
    items: List[WorkflowGuardrailOut]

    class Config:
        from_attributes = True


class WorkflowViolationOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[str]
    action: str
    actor: str
    actor_role: Optional[str]
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
