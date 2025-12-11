"""
PACK UD: API Key & Client Registry Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ApiClientCreate(BaseModel):
    name: str
    client_type: str
    api_key: str
    description: Optional[str] = None


class ApiClientOut(ApiClientCreate):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiClientList(BaseModel):
    total: int
    items: List[ApiClientOut]
