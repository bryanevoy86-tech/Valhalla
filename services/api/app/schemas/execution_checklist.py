"""
PACK CL15: Execution Checklist Schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class ExecutionChecklistItemCreate(BaseModel):
    key: str
    title: str
    description: Optional[str] = None


class ExecutionChecklistItemOut(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
    is_complete: bool
    completed_notes: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionChecklistList(BaseModel):
    total: int
    items: List[ExecutionChecklistItemOut]
