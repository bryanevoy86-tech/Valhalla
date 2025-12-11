"""
PACK AD: SaaS Access Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SaaSPlanModuleIn(BaseModel):
    module_key: str = Field(..., description="Internal module key, e.g. 'wholesale_engine'")


class SaaSPlanBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    currency: str = "USD"


class SaaSPlanCreate(SaaSPlanBase):
    modules: List[SaaSPlanModuleIn] = []


class SaaSPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class SaaSPlanModuleOut(BaseModel):
    id: int
    module_key: str

    class Config:
        from_attributes = True


class SaaSPlanOut(SaaSPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    modules: List[SaaSPlanModuleOut]

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    user_id: int
    plan_id: int
    provider: Optional[str] = None
    provider_sub_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    provider_sub_id: Optional[str] = None


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: str
    provider: Optional[str]
    provider_sub_id: Optional[str]
    started_at: datetime
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True


class AccessCheckOut(BaseModel):
    user_id: int
    module_key: str
    has_access: bool
    plan_code: Optional[str] = None
