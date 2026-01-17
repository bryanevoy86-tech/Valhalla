"""
PACK TI: Financial Stress Early Warning Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FinancialIndicatorCreate(BaseModel):
    name: str
    category: Optional[str] = None
    threshold_type: str  # "above" or "below"
    threshold_value: float
    notes: Optional[str] = None


class FinancialIndicatorOut(FinancialIndicatorCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True


class FinancialStressEventCreate(BaseModel):
    indicator_id: int
    value_at_trigger: float
    description: Optional[str] = None


class FinancialStressEventOut(BaseModel):
    id: int
    indicator_id: int
    date: datetime
    value_at_trigger: float
    description: Optional[str] = None
    resolved: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
