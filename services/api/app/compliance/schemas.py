from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ComplianceBase(BaseModel):
    item_name: str
    category: str
    claimed_amount: float
    risk_score: float | None = None
    rating: str | None = None
    justification: Optional[str] = None


class ComplianceCreate(ComplianceBase):
    pass


class ComplianceResponse(ComplianceBase):
    id: int
    date_logged: datetime

    class Config:
        from_attributes = True
