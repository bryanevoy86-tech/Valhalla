from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ExportJobOut(BaseModel):
    id: int
    job_type: Optional[str] = None
    params: Optional[dict] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    status: str
    attempts: int
    max_attempts: int
    last_error: Optional[str] = None
    next_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExportJobList(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ExportJobOut]
