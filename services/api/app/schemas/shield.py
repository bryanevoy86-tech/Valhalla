from pydantic import BaseModel
from typing import Optional

class ShieldEventCreate(BaseModel):
    event_type: str
    severity: str = "low"
    description: str

class ShieldEventUpdate(BaseModel):
    severity: Optional[str]
    resolved: Optional[str]

class ShieldEventOut(ShieldEventCreate):
    id: int
    resolved: str

    class Config:
        orm_mode = True
