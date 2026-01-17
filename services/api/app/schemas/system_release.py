"""PACK 66: System Release Schemas
Pydantic models for system release validation.
"""

from pydantic import BaseModel


class SystemReleaseBase(BaseModel):
    version: str
    changelog: str
    deployed_by: str


class SystemReleaseCreate(SystemReleaseBase):
    pass


class SystemReleaseOut(SystemReleaseBase):
    id: int

    class Config:
        from_attributes = True
