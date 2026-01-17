"""
PACK 61: Prime Directive Schemas
Pydantic models for prime directive validation.
"""

from pydantic import BaseModel


class PrimeDirectiveBase(BaseModel):
    directive: str


class PrimeDirectiveCreate(PrimeDirectiveBase):
    pass


class PrimeDirectiveOut(PrimeDirectiveBase):
    id: int
    active: bool

    class Config:
        orm_mode = True
