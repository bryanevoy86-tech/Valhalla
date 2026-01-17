"""PACK 85: Industry Engine - Regulatory Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class IndustryRegulationBase(BaseModel):
    industry_id: int
    region: str
    requirements_payload: str


class IndustryRegulationCreate(IndustryRegulationBase):
    pass


class IndustryRegulationOut(IndustryRegulationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
