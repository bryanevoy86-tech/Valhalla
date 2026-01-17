from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExpertReviewBase(BaseModel):
    expert_id: int
    topic: str
    domain: str
    heimdall_recommendation: Optional[str] = None
    expert_recommendation: Optional[str] = None
    alignment_score: float = 1.0
    action_taken: Optional[str] = None
    meeting_date: datetime
    recording_url: Optional[str] = None


class ExpertReviewCreate(ExpertReviewBase):
    pass


class ExpertReviewOut(ExpertReviewBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
