from pydantic import BaseModel
from typing import Optional

class QueenStreamBase(BaseModel):
    name: str
    category: Optional[str] = None
    status: Optional[str] = "active"
    monthly_target: float = 0.0
    current_estimate: float = 0.0
    auto_tax_handled: bool = True
    auto_vault_allocation: bool = True
    notes: Optional[str] = None

class QueenStreamCreate(QueenStreamBase):
    pass

class QueenStreamUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    status: Optional[str]
    monthly_target: Optional[float]
    current_estimate: Optional[float]
    auto_tax_handled: Optional[bool]
    auto_vault_allocation: Optional[bool]
    notes: Optional[str]

class QueenStreamOut(QueenStreamBase):
    id: int

    class Config:
        orm_mode = True
