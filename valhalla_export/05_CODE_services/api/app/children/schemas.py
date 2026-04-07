"""
Pack 54: Children's Hubs + Vault Guardians - Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List

class ChildIn(BaseModel):
    name: str
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    avatar_theme: Optional[str] = None
    save_pct: float = 0.20
    invest_pct: float = 0.00

class ChildOut(ChildIn):
    id: int
    class Config:
        from_attributes = True

class ChoreIn(BaseModel):
    child_id: int
    title: str
    freq: str
    coins: int

class ChoreDone(BaseModel):
    chore_id: int

class WalletOut(BaseModel):
    spendable: int
    savings: int
    invested: int
    fiat_equiv: float

class EarnManual(BaseModel):
    child_id: int
    coins: int
    memo: Optional[str] = None

class SpendReq(BaseModel):
    child_id: int
    coins: int
    memo: Optional[str] = None

class SaveRuleIn(BaseModel):
    child_id: int
    save_pct: float
    invest_pct: float = 0.0

class WishIn(BaseModel):
    child_id: int
    title: str
    priority: int = 3
    coins_target: Optional[int] = None

class IdeaIn(BaseModel):
    child_id: int
    text: str

class DigestOut(BaseModel):
    lines: List[str]
