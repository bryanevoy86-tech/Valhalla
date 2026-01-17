"""PACK 83: Industry Engine - Cost Model Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CostModelBase(BaseModel):
    product_line_id: int
    labor_cost: float | None = None
    material_cost: float | None = None
    overhead_cost: float | None = None
    supply_chain_payload: str | None = None


class CostModelCreate(CostModelBase):
    pass


class CostModelOut(CostModelBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
