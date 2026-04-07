"""PACK 65: Clone Engine Schemas
Pydantic models for clone profile validation.
"""

from pydantic import BaseModel


class CloneProfileBase(BaseModel):
    source_zone: str
    target_zone: str
    include_modules: str


class CloneProfileCreate(CloneProfileBase):
    pass


class CloneProfileOut(CloneProfileBase):
    id: int
    status: str

    class Config:
        from_attributes = True
