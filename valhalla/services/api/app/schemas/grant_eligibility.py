"""
PACK SA: Grant Eligibility Engine Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class RequirementItem(BaseModel):
    item: str
    type: str = Field(..., description="document, status, or eligibility")
    notes: Optional[str] = None


class GrantProfileSchema(BaseModel):
    grant_id: str
    program_name: str
    description: Optional[str] = None
    funding_type: str = Field(default="grant", description="grant, loan, training, support")
    region: Optional[str] = None
    target_groups: Optional[List[str]] = None
    requirements: Optional[List[Dict[str, Any]]] = None
    status: str = Field(default="not_started")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class EligibilityChecklistSchema(BaseModel):
    grant_profile_id: int
    requirement_key: str
    requirement_name: str
    requirement_type: str
    is_completed: bool = False
    is_uploaded: bool = False
    notes: Optional[str] = None
    uploaded_filename: Optional[str] = None

    class Config:
        from_attributes = True


class ChecklistStatusResponse(BaseModel):
    total_requirements: int
    completed: int
    uploaded: int
    missing: int
    progress_percentage: float
