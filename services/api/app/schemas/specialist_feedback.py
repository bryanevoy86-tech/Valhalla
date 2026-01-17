from __future__ import annotations

from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class SpecialistFeedbackBase(BaseModel):
    specialist_role: str = Field(..., max_length=50)
    specialist_name: Optional[str] = Field(default=None, max_length=255)
    notes: str
    suggested_changes: Optional[dict[str, Any]] = None


class SpecialistFeedbackCreate(SpecialistFeedbackBase):
    pass


class SpecialistFeedbackRead(SpecialistFeedbackBase):
    id: UUID
    god_case_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
