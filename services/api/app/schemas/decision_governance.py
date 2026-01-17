"""
PACK AP: Decision Governance Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DecisionPolicyCreate(BaseModel):
    key: str = Field(..., description="Unique key, e.g. approve_deal")
    name: str
    description: Optional[str] = None
    allowed_roles: Optional[str] = Field(
        None,
        description="Comma separated roles: king,queen,odin",
    )
    min_approvals: int = 1


class DecisionPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_roles: Optional[str] = None
    min_approvals: Optional[int] = None
    is_active: Optional[bool] = None


class DecisionPolicyOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    allowed_roles: Optional[str]
    min_approvals: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionCreate(BaseModel):
    policy_key: str
    entity_type: str
    entity_id: str
    initiator: str
    initiator_role: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class DecisionUpdate(BaseModel):
    status: Optional[str] = Field(
        None,
        description="pending, approved, rejected",
    )
    context: Optional[Dict[str, Any]] = None


class DecisionOut(BaseModel):
    id: int
    policy_key: str
    entity_type: str
    entity_id: str
    initiator: str
    initiator_role: Optional[str]
    status: str
    context: Dict[str, Any]
    created_at: datetime
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True
