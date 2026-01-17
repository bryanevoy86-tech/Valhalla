"""
Capital intake schemas for tracking incoming funds.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CapitalIn(BaseModel):
    """Input schema for creating capital intake records"""
    source: str = Field(..., max_length=120)
    currency: str = Field("CAD", max_length=12)
    amount: float
    note: Optional[str] = None


class CapitalOut(CapitalIn):
    """Output schema with database ID"""
    id: int
    
    class Config:
        from_attributes = True
