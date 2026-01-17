"""PACK 89: Household OS - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HouseholdTaskBase(BaseModel):
    name: str
    frequency: str
    assigned_to: str | None = None
    notes: str | None = None
    completed: bool = False


class HouseholdTaskCreate(HouseholdTaskBase):
    pass


class HouseholdTaskOut(HouseholdTaskBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HomeInventoryBase(BaseModel):
    item_name: str
    quantity: int
    min_required: int
    notes: str | None = None


class HomeInventoryCreate(HomeInventoryBase):
    pass


class HomeInventoryOut(HomeInventoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
