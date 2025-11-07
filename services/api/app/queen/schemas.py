"""
Pack 55: Queen's Hub + Fun Fund Vaults - Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict

class QueenOut(BaseModel):
    name: str
    currency: str
    phase: int
    cap_month: float
    tax_rate: float
    class Config:
        from_attributes = True

class AdjustPhaseIn(BaseModel):
    phase: int
    cap_month: Optional[float] = None
    tax_rate: Optional[float] = None

class InflowIn(BaseModel):
    amount: float
    category: Optional[str] = None
    note: Optional[str] = None

class SpendIn(BaseModel):
    amount: float
    category: str
    note: Optional[str] = None

class VaultOut(BaseModel):
    balance: float
    currency: str

class CapStatus(BaseModel):
    yyyymm: str
    allowed: float
    used: float
    remaining: float
