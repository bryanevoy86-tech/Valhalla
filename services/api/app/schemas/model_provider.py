"""
PACK CL12: Model Provider Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelProviderBase(BaseModel):
    name: str = Field(..., description="Short name like 'gpt-5.1-thinking'.")
    vendor: str = Field(..., description="Provider name like 'openai'.")
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Backend configuration (endpoint, model_id, etc.).",
    )
    active: bool = Field(True, description="Whether this provider can be used.")
    default_for_heimdall: bool = Field(
        False,
        description="If true, Heimdall uses this provider by default.",
    )


class ModelProviderCreate(ModelProviderBase):
    pass


class ModelProviderOut(ModelProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelProviderList(BaseModel):
    total: int
    items: List[ModelProviderOut]
