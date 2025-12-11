"""PACK 81: Industry Engine - Registry Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class IndustryProfileBase(BaseModel):
    name: str
    description: str | None = None
    config_payload: str


class IndustryProfileCreate(IndustryProfileBase):
    pass


class IndustryProfileOut(IndustryProfileBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
