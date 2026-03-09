from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContractorRankBase(BaseModel):
    code: str
    name: str
    min_score: float = 0.0
    max_score: float = 100.0
    perks: Optional[str] = None


class ContractorRankCreate(ContractorRankBase):
    pass


class ContractorRankOut(ContractorRankBase):
    id: int

    class Config:
        orm_mode = True


class ContractorLoyaltyVaultBase(BaseModel):
    contractor_id: int
    contractor_name: str
    rank_code: str
    loyalty_score: float = 0.0
    vault_balance: float = 0.0
    jv_eligible: bool = False
    notes: Optional[str] = None


class ContractorLoyaltyVaultCreate(ContractorLoyaltyVaultBase):
    pass


class ContractorLoyaltyVaultUpdate(BaseModel):
    rank_code: Optional[str]
    loyalty_score: Optional[float]
    vault_balance: Optional[float]
    jv_eligible: Optional[bool]
    notes: Optional[str]


class ContractorLoyaltyVaultOut(ContractorLoyaltyVaultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
