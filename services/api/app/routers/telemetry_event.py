"""
PACK L0-06: Telemetry Events Router
Provides endpoints for ingesting and querying telemetry events.
Marked as stable API (STABLE CONTRACT).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.schemas.telemetry_event import (
    TelemetryEventCreate,
    TelemetryEventOut,
    TelemetryEventQuery,
    TelemetryEventList,
    TelemetrySummary,
)
from app.services.telemetry_event import TelemetryService, get_telemetry_service


router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/events", response_model=TelemetryEventOut)
def write_telemetry_event(
    payload: TelemetryEventCreate,
    db: Session = Depends(get_db),
) -> TelemetryEventOut:
    """
    Write a telemetry event to the centralized event store.
    
    Use this endpoint to log system events (health checks, security actions, jobs, etc.)
    with optional correlation IDs for distributed tracing.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    **Important:** Do NOT include secrets, passwords, API keys, or PII in the payload.
    All telemetry data is considered audit-public.
    
    Args:
        payload: TelemetryEventCreate with event data
        db: Database session (injected)
    
    Returns:
        TelemetryEventOut: The created event with timestamp and ID
    
    Example:
        ```json
        POST /telemetry/events
        {
          "event_type": "health.check",
          "source": "system_health",
          "severity": "info",
          "category": "system",
          "message": "Health check passed",
          "correlation_id": "req-123",
          "payload": {"db_ok": true, "uptime_s": 3600}
        }
        ```
    """
    service = get_telemetry_service(db)
    return service.write(payload)


@router.get("/events", response_model=TelemetryEventList)
def list_telemetry_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    severity: Optional[str] = Query(None, description="Filter by severity (debug, info, warning, error, critical)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID (trace)"),
    actor_id: Optional[str] = Query(None, description="Filter by actor"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    limit: int = Query(100, ge=1, le=1000, description="Max results (1-1000)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> TelemetryEventList:
    """
    List telemetry events with optional filtering and pagination.
    
    Returns recent events (newest first) optionally filtered by event type, source,
    severity, category, correlation ID, or actor.
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Args:
        event_type: Filter by event type (e.g., 'health.check')
        source: Filter by source (e.g., 'system_health')
        severity: Filter by severity level
        category: Filter by category
        correlation_id: Filter by correlation ID for trace lookup
        actor_id: Filter by actor
        tenant_id: Filter by tenant
        limit: Max results (1-1000, default 100)
        offset: Pagination offset
        db: Database session (injected)
    
    Returns:
        TelemetryEventList: Total count and list of matching events
    
    Example:
        ```
        GET /telemetry/events?severity=error&limit=50
        GET /telemetry/events?correlation_id=req-123
        ```
    """
    query = TelemetryEventQuery(
        event_type=event_type,
        source=source,
        severity=severity,
        category=category,
        correlation_id=correlation_id,
        actor_id=actor_id,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    service = get_telemetry_service(db)
    items, total = service.list(query)
    return TelemetryEventList(total=total, items=items)


@router.get("/trace/{correlation_id}")
def get_trace(
    correlation_id: str,
    db: Session = Depends(get_db),
) -> TelemetryEventList:
    """
    Get all events associated with a correlation ID (distributed trace).
    
    Useful for debugging requests across multiple services and components.
    
    **STABLE CONTRACT:** This endpoint will remain available.
    
    Args:
        correlation_id: Correlation ID to trace
        db: Database session (injected)
    
    Returns:
        TelemetryEventList: All events in the trace (chronological order)
    
    Example:
        ```
        GET /telemetry/trace/req-123-abc
        ```
    """
    service = get_telemetry_service(db)
    items = service.get_by_correlation_id(correlation_id)
    return TelemetryEventList(total=len(items), items=items)


@router.get("/summary", response_model=TelemetrySummary)
def get_telemetry_summary(
    db: Session = Depends(get_db),
) -> TelemetrySummary:
    """
    Get telemetry summary statistics.
    
    Returns aggregated statistics about events, useful for dashboards and SLO reporting.
    Includes event counts by severity/source/category, recent error rate, and latest error.
    
    **STABLE CONTRACT:** Response format will not change.
    
    Args:
        db: Database session (injected)
    
    Returns:
        TelemetrySummary: Statistics about telemetry data
    
    Example:
        ```json
        GET /telemetry/summary
        {
          "total_events": 10245,
          "events_by_severity": {"info": 9500, "warning": 600, "error": 145},
          "events_by_source": {"system_health": 2000, "job_runner": 3000, ...},
          "errors_last_hour": 12,
          "warnings_last_hour": 45,
          "latest_error": {...}
        }
        ```
    """
    service = get_telemetry_service(db)
    return service.get_summary()
