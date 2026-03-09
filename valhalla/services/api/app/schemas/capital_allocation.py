"""
PACK 62: Capital Allocation Schemas
Pydantic models for capital allocation validation.
"""

from pydantic import BaseModel


class CapitalAllocationBase(BaseModel):
    arbitrage_pct: float
    vault_pct: float
    shield_pct: float


class CapitalAllocationCreate(CapitalAllocationBase):
    pass


class CapitalAllocationOut(CapitalAllocationBase):
    id: int

    class Config:
        orm_mode = True
