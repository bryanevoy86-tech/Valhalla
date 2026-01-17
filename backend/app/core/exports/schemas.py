from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime

ExportStatus = Literal["queued", "running", "done", "failed"]


class ExportJobCreate(BaseModel):
    export_type: str = Field(..., description="e.g. 'buyers', 'leads', 'properties'")
    params: Dict[str, Any] = {}


class ExportJobOut(BaseModel):
    id: str
    status: ExportStatus
    export_type: str
    created_at: datetime
    updated_at: datetime
    result_url: Optional[str] = None
    error: Optional[str] = None
