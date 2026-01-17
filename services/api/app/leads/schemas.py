"""
Pydantic schemas for Lead management.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    source: str = Field(..., min_length=1, max_length=100)
    status: str | None = Field(default="new", max_length=50)


class LeadOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)
