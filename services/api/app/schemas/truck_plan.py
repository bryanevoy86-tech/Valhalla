from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TruckPlanBase(BaseModel):
    name: Optional[str] = "Valhalla Truck"
    target_price: float
    wrap_budget: float = 0.0
    extras_budget: float = 0.0
    business_credit_target: float = 0.0
    current_business_credit: float = 0.0
    funfund_contribution_target: float = 0.0
    funfund_contributed: float = 0.0
    status: Optional[str] = "planning"
    notes: Optional[str] = None


class TruckPlanCreate(TruckPlanBase):
    pass


class TruckPlanUpdate(BaseModel):
    name: Optional[str]
    target_price: Optional[float]
    wrap_budget: Optional[float]
    extras_budget: Optional[float]
    business_credit_target: Optional[float]
    current_business_credit: Optional[float]
    funfund_contribution_target: Optional[float]
    funfund_contributed: Optional[float]
    status: Optional[str]
    notes: Optional[str]


class TruckPlanOut(TruckPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
