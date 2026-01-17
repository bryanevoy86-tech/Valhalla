"""
PACK TR: Security Action Schemas
Request/response models for action workflow.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class SecurityActionRequestCreate(BaseModel):
    """Create a security action request."""
    requested_by: str       # Heimdall, Tyr, human:<id>
    action_type: str        # block_entity, set_mode, update_policy
    payload: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityActionRequestUpdate(BaseModel):
    """Approve or reject action request."""
    status: str             # approved, rejected, executed
    approved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityActionRequestOut(BaseModel):
    """Security action request response."""
    id: int
    created_at: datetime
    updated_at: datetime
    requested_by: str
    approved_by: Optional[str]
    action_type: str
    payload: Optional[dict]
    status: str
    executed_at: Optional[datetime]
    resolution_notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class SecurityActionRequestList(BaseModel):
    """List of action requests."""
    total: int
    pending: int
    items: List[SecurityActionRequestOut]

    model_config = ConfigDict(from_attributes=True)
