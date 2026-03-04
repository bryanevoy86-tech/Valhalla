"""
PACK CL14: Correction Plan Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CorrectionPlanCreate(BaseModel):
    plan_id: str
    run_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    requires_human_approval: bool = True


class CorrectionPlanOut(BaseModel):
    plan_id: str
    run_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    status: str
    requires_human_approval: bool

    class Config:
        from_attributes = True


class CorrectionPlanList(BaseModel):
    total: int
    items: List[CorrectionPlanOut]
