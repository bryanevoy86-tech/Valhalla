"""
PACK L0-08: Job Schemas
Pydantic models for job creation, updates, and querying.
Marked as stable API (STABLE CONTRACT).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ScheduledJobCreate(BaseModel):
    """Schema for creating a scheduled job."""
    
    name: str = Field(..., description="Job name (e.g., 'weekly_empire_snapshot')")
    category: str = Field(default="general", description="Category (kpi, snapshot, legal, etc.)")
    schedule: str = Field(..., description="Cron expression (e.g., '0 3 * * MON')")
    task_path: str = Field(..., description="Python path to execute (e.g., 'tasks.snapshots.create_weekly')")
    args: Optional[Dict[str, Any]] = Field(None, description="JSON arguments for task")
    active: bool = Field(default=True, description="Whether job is active")
    
    class Config:
        from_attributes = True


class ScheduledJobOut(ScheduledJobCreate):
    """Schema for scheduled job response."""
    
    id: int = Field(..., description="Job ID")
    last_run_at: Optional[datetime] = Field(None, description="Last execution time")
    last_status: Optional[str] = Field(None, description="Last execution status")
    last_error: Optional[str] = Field(None, description="Last error message")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class Config:
        from_attributes = True


class SystemCheckJobCreate(BaseModel):
    """Schema for creating a system check job."""
    
    name: str = Field(..., description="Check name")
    scope: str = Field(..., description="Scope to check (system, module, etc.)")
    scope_code: Optional[str] = Field(None, description="Scope code identifier")
    schedule: str = Field(default="weekly", description="Schedule (daily, weekly, monthly)")
    active: bool = Field(default=True, description="Whether check is active")
    notes: Optional[str] = Field(None, description="Notes about this check")
    
    class Config:
        from_attributes = True


class SystemCheckJobOut(SystemCheckJobCreate):
    """Schema for system check job response."""
    
    id: int = Field(..., description="Job ID")
    last_run_at: Optional[datetime] = Field(None, description="Last execution time")
    last_status: Optional[str] = Field(None, description="Last execution status")
    last_health_score: float = Field(default=1.0, description="Last health score (0-1)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class Config:
        from_attributes = True


class TrainingJobCreate(BaseModel):
    """Schema for creating a training job."""
    
    job_type: str = Field(..., description="Type of training (embedding, classifier, etc.)")
    target_module: str = Field(..., description="Module to train (e.g., 'heimdall_core')")
    priority: int = Field(default=10, ge=1, le=100, description="Job priority (1-100, higher = more urgent)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Training parameters")
    
    class Config:
        from_attributes = True


class TrainingJobOut(TrainingJobCreate):
    """Schema for training job response."""
    
    id: int = Field(..., description="Job ID")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress (0-1)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start time")
    finished_at: Optional[datetime] = Field(None, description="Finish time")
    
    class Config:
        from_attributes = True


class JobQuery(BaseModel):
    """Schema for querying jobs."""
    
    status: Optional[JobStatus] = Field(None, description="Filter by status")
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    
    class Config:
        from_attributes = True


class JobList(BaseModel):
    """Response for job list endpoint."""
    
    total: int = Field(..., description="Total count")
    items: List[Dict[str, Any]] = Field(..., description="Job list")
    
    class Config:
        from_attributes = True
