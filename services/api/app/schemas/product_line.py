"""PACK 82: Industry Engine - Product Line Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductLineBase(BaseModel):
    industry_id: int
    name: str
    description: str | None = None
    cost_structure: str | None = None
    retail_price: float | None = None


class ProductLineCreate(ProductLineBase):
    pass


class ProductLineOut(ProductLineBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
