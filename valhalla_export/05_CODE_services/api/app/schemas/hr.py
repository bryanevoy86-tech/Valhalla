"""PACK 92: HR Engine - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EmployeeBase(BaseModel):
    name: str
    role: str
    email: str
    status: str = "active"


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PerformanceLogBase(BaseModel):
    employee_id: int
    score: int
    notes: str | None = None


class PerformanceLogCreate(PerformanceLogBase):
    pass


class PerformanceLogOut(PerformanceLogBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OnboardingDocumentBase(BaseModel):
    employee_id: int
    doc_type: str
    doc_payload: str


class OnboardingDocumentCreate(OnboardingDocumentBase):
    pass


class OnboardingDocumentOut(OnboardingDocumentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
