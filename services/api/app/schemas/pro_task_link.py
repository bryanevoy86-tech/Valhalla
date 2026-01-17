# services/api/app/schemas/pro_task_link.py

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ProfessionalTaskLinkIn(BaseModel):
    professional_id: int
    deal_id: int
    task_id: int
    status: str = Field(default="open", description="Task status: open, in_progress, blocked, done")


class ProfessionalTaskLinkOut(ProfessionalTaskLinkIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
