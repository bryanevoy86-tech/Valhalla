"""
PACK CL13: Self-Supervision Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SelfSupervisionFindingCreate(BaseModel):
    finding_type: str
    severity: str = "medium"
    title: str
    detail: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SelfSupervisionRunCreate(BaseModel):
    run_id: str = Field(..., description="Client-generated run id (uuid recommended)")
    trigger: Optional[str] = None
    scope: Optional[str] = None
    summary: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    findings: List[SelfSupervisionFindingCreate] = Field(default_factory=list)


class SelfSupervisionRunOut(BaseModel):
    run_id: str
    trigger: Optional[str] = None
    scope: Optional[str] = None
    summary: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SelfSupervisionFindingOut(BaseModel):
    run_id: str
    finding_type: str
    severity: str
    title: str
    detail: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool

    class Config:
        from_attributes = True


class SelfSupervisionRunList(BaseModel):
    total: int
    items: List[SelfSupervisionRunOut]


class SelfSupervisionFindingList(BaseModel):
    total: int
    items: List[SelfSupervisionFindingOut]
