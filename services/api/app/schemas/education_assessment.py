"""PACK 80: Education SaaS - Assessment Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    classroom_id: int
    title: str
    instructions: str
    due_date: datetime | None = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentOut(AssignmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionBase(BaseModel):
    assignment_id: int
    student_id: int
    content_payload: str


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionOut(SubmissionBase):
    id: int
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GradeBase(BaseModel):
    submission_id: int
    score: float
    feedback: str | None = None


class GradeCreate(GradeBase):
    pass


class GradeOut(GradeBase):
    id: int
    graded_at: datetime

    model_config = ConfigDict(from_attributes=True)
