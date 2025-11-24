from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComplianceSignalCreate(BaseModel):
    deal_id: Optional[int] = None
    source: str
    severity: str = "info"
    code: Optional[str] = None
    message: str
    score: float = 0.0

class ComplianceSignalOut(ComplianceSignalCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
