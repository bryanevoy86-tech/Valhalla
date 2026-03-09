from pydantic import BaseModel
from typing import Optional

class StaffBase(BaseModel):
    full_name: str
    role: str
    region: str
    pay_rate: float

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    role: Optional[str]
    region: Optional[str]
    pay_rate: Optional[float]
    status: Optional[str]
    reliability_score: Optional[float]
    skill_score: Optional[float]
    attitude_score: Optional[float]

class StaffOut(StaffBase):
    id: int
    status: str
    reliability_score: float
    skill_score: float
    attitude_score: float

    class Config:
        orm_mode = True
