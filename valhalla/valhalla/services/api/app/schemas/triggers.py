"""
PACK CI6: Trigger & Threshold Engine Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TriggerRuleIn(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    condition: Dict[str, Any]
    action: Dict[str, Any]
    active: bool = True


class TriggerRuleOut(TriggerRuleIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriggerRuleList(BaseModel):
    total: int
    items: List[TriggerRuleOut]


class TriggerEventOut(BaseModel):
    id: int
    rule_id: int
    status: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TriggerEventList(BaseModel):
    total: int
    items: List[TriggerEventOut]


class TriggerEvaluationRequest(BaseModel):
    rule_id: int
    context: Dict[str, Any]
