"""
PACK AB: Education Engine Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str
    subject: Optional[str] = Field(None, description="real_estate, money, mindset, etc.")
    level: Optional[str] = Field(None, description="beginner, intermediate, advanced")
    description: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CourseOut(BaseModel):
    id: int
    title: str
    subject: Optional[str]
    level: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    course_id: int
    title: str
    summary: Optional[str] = None
    order_index: int = 1


class LessonOut(BaseModel):
    id: int
    course_id: int
    title: str
    summary: Optional[str]
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    learner_id: int
    course_id: int


class EnrollmentUpdate(BaseModel):
    lessons_completed: Optional[int] = None
    is_active: Optional[bool] = None


class EnrollmentOut(BaseModel):
    id: int
    learner_id: int
    course_id: int
    lessons_completed: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
