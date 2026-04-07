"""
Pack 56: King's Hub + Adaptive Vault Scaling - Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict

class RuleSetIn(BaseModel):
    reinvest_pct: float
    fun_pct: float
    bahamas_pct: float
    reserves_pct: float

class InflowIn(BaseModel):
    amount: float
    note: Optional[str] = None

class SpendIn(BaseModel):
    vault: str  # Reserves|Reinvest|Bahamas|Fun
    amount: float
    note: Optional[str] = None

class StatusOut(BaseModel):
    currency: str
    vaults: Dict[str, float]
    rules: Dict[str, float]
    bahamas_progress: Dict[str, float]
