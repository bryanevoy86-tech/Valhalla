"""
Pydantic schemas for payments.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class PaymentCreate(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)

class PaymentOut(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
