from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChildBase(BaseModel):
    name: str
    nickname: Optional[str] = None
    status: Optional[str] = "active"

class ChildCreate(ChildBase):
    pass

class ChildUpdate(BaseModel):
    name: Optional[str]
    nickname: Optional[str]
    status: Optional[str]

class ChildOut(ChildBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ChoreBase(BaseModel):
    title: str
    description: Optional[str] = None
    coin_value: float = 0.0
    frequency: Optional[str] = "ad-hoc"
    status: Optional[str] = "active"
    child_id: Optional[int] = None

class ChoreCreate(ChoreBase):
    pass

class ChoreUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    coin_value: Optional[float]
    frequency: Optional[str]
    status: Optional[str]
    child_id: Optional[int]

class ChoreOut(ChoreBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class CoinLedgerCreate(BaseModel):
    child_id: int
    amount: float
    reason: Optional[str] = None
    entry_type: Optional[str] = "earn"

class CoinLedgerOut(CoinLedgerCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
