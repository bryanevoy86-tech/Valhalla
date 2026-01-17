from pydantic import BaseModel
from typing import Optional

class TrustBase(BaseModel):
    name: str
    jurisdiction: str

class TrustCreate(TrustBase):
    tax_exempt: bool = False
    routing_priority: int = 1

class TrustUpdate(BaseModel):
    name: Optional[str]
    jurisdiction: Optional[str]
    status: Optional[str]
    routing_priority: Optional[int]
    tax_exempt: Optional[bool]
    vault_balance: Optional[float]

class TrustOut(TrustBase):
    id: int
    status: str
    routing_priority: int
    tax_exempt: bool
    vault_balance: float

    class Config:
        orm_mode = True
