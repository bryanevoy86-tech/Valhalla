"""
PACK Y: Dispo Engine Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DispoBuyerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    buy_box_summary: Optional[str] = None
    notes: Optional[str] = None


class DispoBuyerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    buy_box_summary: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DispoBuyerOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    buy_box_summary: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DispoAssignmentCreate(BaseModel):
    pipeline_id: int
    buyer_id: int
    status: str = Field(default="offered")
    assignment_price: Optional[float] = None
    assignment_fee: Optional[float] = None
    notes: Optional[str] = None


class DispoAssignmentUpdate(BaseModel):
    status: Optional[str] = None
    assignment_price: Optional[float] = None
    assignment_fee: Optional[float] = None
    notes: Optional[str] = None


class DispoAssignmentOut(BaseModel):
    id: int
    pipeline_id: int
    buyer_id: int
    status: str
    assignment_price: Optional[float]
    assignment_fee: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
