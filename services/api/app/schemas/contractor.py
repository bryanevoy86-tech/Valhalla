from pydantic import BaseModel
from typing import Optional

class ContractorBase(BaseModel):
    company_name: str
    contact_person: str
    region: str

class ContractorCreate(ContractorBase):
    pass

class ContractorUpdate(BaseModel):
    loyalty_rank: Optional[str]
    jobs_completed: Optional[int]
    quality_score: Optional[float]
    speed_score: Optional[float]
    attitude_score: Optional[float]

class ContractorOut(ContractorBase):
    id: int
    loyalty_rank: str
    jobs_completed: int
    quality_score: float
    speed_score: float
    attitude_score: float

    class Config:
        orm_mode = True
