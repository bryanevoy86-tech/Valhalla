"""
PACK AR: Heimdall Workload Balancer Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HeimdallJobCreate(BaseModel):
    job_type: str
    source: Optional[str] = None
    priority: str = Field("normal", description="low, normal, high, critical")
    payload: Dict[str, Any] = Field(default_factory=dict)


class HeimdallJobUpdate(BaseModel):
    status: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class HeimdallJobOut(BaseModel):
    id: int
    job_type: str
    source: Optional[str]
    priority: str
    status: str
    payload: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class HeimdallWorkloadConfigCreate(BaseModel):
    job_type: str
    enabled: bool = True
    max_concurrent: Optional[int] = None
    notes: Optional[str] = None


class HeimdallWorkloadConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    max_concurrent: Optional[int] = None
    notes: Optional[str] = None


class HeimdallWorkloadConfigOut(BaseModel):
    id: int
    job_type: str
    enabled: bool
    max_concurrent: Optional[int]
    notes: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class HeimdallQueueStats(BaseModel):
    total_jobs: int
    queued: int
    in_progress: int
    completed: int
    failed: int
