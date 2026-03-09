"""
PACK 63: Evolution Engine Schemas
Pydantic models for evolution event validation.
"""

from pydantic import BaseModel


class EvolutionEventBase(BaseModel):
    trigger: str
    description: str


class EvolutionEventCreate(EvolutionEventBase):
    pass


class EvolutionEventOut(EvolutionEventBase):
    id: int

    class Config:
        orm_mode = True
