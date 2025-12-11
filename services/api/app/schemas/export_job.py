"""
PACK UH: Export & Snapshot Job Engine Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel


class ExportJobCreate(BaseModel):
    job_type: str
    filter_params: Optional[Dict[str, Any]] = None
    requested_by: Optional[str] = None


class ExportJobOut(ExportJobCreate):
    id: int
    created_at: datetime
    completed_at: Optional[datetime]
    status: str
    storage_url: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ExportJobList(BaseModel):
    total: int
    items: List[ExportJobOut]
