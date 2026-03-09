"""
PACK 60: System Finalization Schemas
Pydantic models for system integrity seal validation.
"""

from pydantic import BaseModel


class SystemIntegritySealBase(BaseModel):
    seal_hash: str
    schema_version: str


class SystemIntegritySealCreate(SystemIntegritySealBase):
    pass


class SystemIntegritySealOut(SystemIntegritySealBase):
    id: int
    active: bool

    class Config:
        orm_mode = True
