"""PACK 77: Education SaaS - Org Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SchoolBase(BaseModel):
    name: str
    district: str | None = None
    notes: str | None = None


class SchoolCreate(SchoolBase):
    pass


class SchoolOut(SchoolBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassroomBase(BaseModel):
    school_id: int
    name: str
    grade_level: str | None = None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomOut(ClassroomBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherBase(BaseModel):
    school_id: int
    name: str
    subject: str | None = None


class TeacherCreate(TeacherBase):
    pass


class TeacherOut(TeacherBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
