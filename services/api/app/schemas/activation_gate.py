"""
PACK CL17: Activation Gate Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ActivationGateUpsert(BaseModel):
    gate_key: str
    title: str
    description: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    is_enabled: bool = False


class ActivationGateLock(BaseModel):
    is_locked: bool
    lock_reason: Optional[str] = None


class ActivationGateOut(BaseModel):
    gate_key: str
    title: str
    description: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    is_enabled: bool
    is_locked: bool
    lock_reason: Optional[str] = None

    class Config:
        from_attributes = True


class ActivationGateList(BaseModel):
    total: int
    items: List[ActivationGateOut]
