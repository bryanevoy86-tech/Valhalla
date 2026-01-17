"""
PACK L0-06: Telemetry Schemas
Pydantic models for telemetry event ingestion and querying.
Marked as stable API (STABLE CONTRACT).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TelemetryEventCreate(BaseModel):
    """
    Schema for creating a new telemetry event.
    
    Accepts structured event data with optional correlation ID for distributed tracing.
    Do NOT include secrets, passwords, or PII in payload.
    """
    
    event_type: str = Field(..., description="Event type (e.g., 'health.check', 'log.write')")
    source: str = Field(..., description="Source of event (e.g., 'system_health', 'job_runner')")
    severity: str = Field(default="info", description="Severity level: debug, info, warning, error, critical")
    category: Optional[str] = Field(None, description="Category for grouping (auth, security, finance, system)")
    
    message: Optional[str] = Field(None, description="Human-readable message")
    payload: Optional[Dict[str, Any]] = Field(None, description="Structured data (no secrets/PII)")
    
    # Tracing
    correlation_id: Optional[str] = Field(None, description="Correlation ID for distributed tracing")
    parent_trace_id: Optional[str] = Field(None, description="Parent span ID for tracing")
    
    # Context
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    actor_id: Optional[str] = Field(None, description="Actor identifier (user, system, job, etc.)")
    actor_type: Optional[str] = Field(None, description="Type of actor (user, system, job, ai)")
    
    # Metrics
    duration_ms: Optional[int] = Field(None, description="Operation duration in milliseconds")
    status: Optional[str] = Field(None, description="Operation status (ok, error, timeout, etc.)")
    
    class Config:
        from_attributes = True


class TelemetryEventOut(TelemetryEventCreate):
    """
    Schema for returning telemetry event from database.
    Includes database-generated fields.
    """
    
    id: int = Field(..., description="Event ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    
    class Config:
        from_attributes = True


class TelemetryEventQuery(BaseModel):
    """
    Schema for querying telemetry events.
    Supports filtering and pagination.
    """
    
    event_type: Optional[str] = Field(None, description="Filter by event type")
    source: Optional[str] = Field(None, description="Filter by source")
    severity: Optional[str] = Field(None, description="Filter by severity")
    category: Optional[str] = Field(None, description="Filter by category")
    correlation_id: Optional[str] = Field(None, description="Filter by correlation ID")
    actor_id: Optional[str] = Field(None, description="Filter by actor")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant")
    
    limit: int = Field(default=100, ge=1, le=1000, description="Max results (1-1000)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    
    class Config:
        from_attributes = True


class TelemetryEventList(BaseModel):
    """
    Response model for listing telemetry events.
    """
    
    total: int = Field(..., description="Total count of matching events")
    items: List[TelemetryEventOut] = Field(..., description="List of events")
    
    class Config:
        from_attributes = True


class TelemetrySummary(BaseModel):
    """
    Summary statistics for telemetry data.
    Useful for dashboards and SLO reporting.
    """
    
    total_events: int = Field(..., description="Total events in database")
    events_by_severity: Dict[str, int] = Field(..., description="Count by severity level")
    events_by_source: Dict[str, int] = Field(..., description="Count by source")
    events_by_category: Dict[str, int] = Field(..., description="Count by category")
    
    errors_last_hour: int = Field(..., description="Error count in last hour")
    warnings_last_hour: int = Field(..., description="Warning count in last hour")
    
    latest_error: Optional[TelemetryEventOut] = Field(None, description="Most recent error event")
    
    class Config:
        from_attributes = True
