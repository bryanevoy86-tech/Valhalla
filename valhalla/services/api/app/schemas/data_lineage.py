"""
PACK AM: Data Lineage Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DataLineageCreate(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    source: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataLineageOut(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    source: Optional[str]
    description: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
