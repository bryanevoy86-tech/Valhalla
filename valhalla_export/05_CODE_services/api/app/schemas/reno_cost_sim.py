"""PACK 71: Reno Cost Simulator Schemas
Pydantic models for renovation cost simulation validation.
"""

from pydantic import BaseModel


class RenoCostSimBase(BaseModel):
    blueprint_id: int
    input_payload: str
    low_estimate: float
    mid_estimate: float
    high_estimate: float


class RenoCostSimCreate(RenoCostSimBase):
    pass


class RenoCostSimOut(RenoCostSimBase):
    id: int

    class Config:
        from_attributes = True
