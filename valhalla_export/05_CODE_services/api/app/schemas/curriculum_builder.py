"""PACK 79: Curriculum Builder - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CurriculumUnitBase(BaseModel):
    title: str
    grade_level: str | None = None
    subject: str | None = None
    content_payload: str | None = None


class CurriculumUnitCreate(CurriculumUnitBase):
    pass


class CurriculumUnitOut(CurriculumUnitBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignedUnitBase(BaseModel):
    classroom_id: int
    unit_id: int


class AssignedUnitCreate(AssignedUnitBase):
    pass


class AssignedUnitOut(AssignedUnitBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
