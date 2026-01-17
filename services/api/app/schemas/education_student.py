"""PACK 78: Education SaaS - Student Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    classroom_id: int
    name: str
    age: int | None = None
    notes: str | None = None


class StudentCreate(StudentBase):
    pass


class StudentOut(StudentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParentAccountBase(BaseModel):
    student_id: int
    parent_name: str
    contact_email: str | None = None


class ParentAccountCreate(ParentAccountBase):
    pass


class ParentAccountOut(ParentAccountBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
