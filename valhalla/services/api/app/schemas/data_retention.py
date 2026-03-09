"""
PACK UI: Data Retention Policy Registry Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DataRetentionSet(BaseModel):
    category: str
    days_to_keep: int
    enabled: bool = True
    description: Optional[str] = None


class DataRetentionOut(DataRetentionSet):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataRetentionList(BaseModel):
    total: int
    items: List[DataRetentionOut]
