from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LegacyBase(BaseModel):
    name: str

class LegacyCreate(LegacyBase):
    auto_clone_enabled: bool = True

class LegacyUpdate(BaseModel):
    status: Optional[str]
    readiness_score: Optional[int]
    auto_clone_enabled: Optional[bool]

class LegacyOut(LegacyBase):
    id: int
    status: str
    readiness_score: int
    auto_clone_enabled: bool
    last_clone_at: Optional[datetime]

    class Config:
        orm_mode = True
