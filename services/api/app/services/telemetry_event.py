"""
PACK L0-06: Telemetry Service
Manages telemetry event ingestion, querying, and analysis.
Marked as stable API (STABLE CONTRACT).
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.telemetry_event import TelemetryEvent
from app.schemas.telemetry_event import (
    TelemetryEventCreate,
    TelemetryEventOut,
    TelemetryEventQuery,
    TelemetrySummary,
)


class TelemetryService:
    """
    Service for managing telemetry events.
    
    Provides ingestion, querying, and analysis of system events.
    All methods are typed and include docstrings.
    """
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
    
    def write(self, payload: TelemetryEventCreate) -> TelemetryEventOut:
        """
        Write a telemetry event to the database.
        
        STABLE CONTRACT: Return type and format will not change.
        
        Args:
            payload: TelemetryEventCreate with event data
        
        Returns:
            TelemetryEventOut: The created event with timestamp and ID
        """
        obj = TelemetryEvent(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return TelemetryEventOut.from_orm(obj)
    
    def list(self, query: TelemetryEventQuery) -> Tuple[List[TelemetryEventOut], int]:
        """
        List telemetry events with optional filtering.
        
        STABLE CONTRACT: Result format and ordering will not change.
        
        Args:
            query: TelemetryEventQuery with filters and pagination
        
        Returns:
            Tuple of (items: List[TelemetryEventOut], total: int)
                - items: List of matching events (newest first)
                - total: Total count of matching events
        """
        q = self.db.query(TelemetryEvent)
        
        # Apply filters
        if query.event_type:
            q = q.filter(TelemetryEvent.event_type == query.event_type)
        if query.source:
            q = q.filter(TelemetryEvent.source == query.source)
        if query.severity:
            q = q.filter(TelemetryEvent.severity == query.severity)
        if query.category:
            q = q.filter(TelemetryEvent.category == query.category)
        if query.correlation_id:
            q = q.filter(TelemetryEvent.correlation_id == query.correlation_id)
        if query.actor_id:
            q = q.filter(TelemetryEvent.actor_id == query.actor_id)
        if query.tenant_id:
            q = q.filter(TelemetryEvent.tenant_id == query.tenant_id)
        
        total = q.count()
        
        # Order by newest first and apply pagination
        items = (
            q.order_by(desc(TelemetryEvent.timestamp))
            .offset(query.offset)
            .limit(query.limit)
            .all()
        )
        
        return [TelemetryEventOut.from_orm(item) for item in items], total
    
    def get_by_correlation_id(self, correlation_id: str) -> List[TelemetryEventOut]:
        """
        Get all events with a given correlation ID (trace).
        
        Useful for debugging distributed request flows.
        
        Args:
            correlation_id: Correlation ID to search for
        
        Returns:
            List of events in chronological order
        """
        items = (
            self.db.query(TelemetryEvent)
            .filter(TelemetryEvent.correlation_id == correlation_id)
            .order_by(TelemetryEvent.timestamp)
            .all()
        )
        return [TelemetryEventOut.from_orm(item) for item in items]
    
    def get_summary(self) -> TelemetrySummary:
        """
        Get summary statistics about telemetry data.
        
        Useful for dashboards, SLO reporting, and health checks.
        
        STABLE CONTRACT: Response format will not change.
        
        Returns:
            TelemetrySummary with counts and recent error info
        """
        total_events = self.db.query(TelemetryEvent).count()
        
        # Count by severity
        severity_counts = {}
        for severity in ["debug", "info", "warning", "error", "critical"]:
            count = (
                self.db.query(TelemetryEvent)
                .filter(TelemetryEvent.severity == severity)
                .count()
            )
            if count > 0:
                severity_counts[severity] = count
        
        # Count by source (top sources only)
        sources = self.db.query(TelemetryEvent.source).distinct().all()
        source_counts = {}
        for (source,) in sources:
            count = (
                self.db.query(TelemetryEvent)
                .filter(TelemetryEvent.source == source)
                .count()
            )
            source_counts[source] = count
        
        # Count by category
        categories = self.db.query(TelemetryEvent.category).distinct().all()
        category_counts = {}
        for (category,) in categories:
            if category:
                count = (
                    self.db.query(TelemetryEvent)
                    .filter(TelemetryEvent.category == category)
                    .count()
                )
                category_counts[category] = count
        
        # Errors in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        errors_last_hour = (
            self.db.query(TelemetryEvent)
            .filter(
                and_(
                    TelemetryEvent.timestamp >= one_hour_ago,
                    TelemetryEvent.severity == "error",
                )
            )
            .count()
        )
        
        warnings_last_hour = (
            self.db.query(TelemetryEvent)
            .filter(
                and_(
                    TelemetryEvent.timestamp >= one_hour_ago,
                    TelemetryEvent.severity == "warning",
                )
            )
            .count()
        )
        
        # Latest error
        latest_error = (
            self.db.query(TelemetryEvent)
            .filter(TelemetryEvent.severity == "error")
            .order_by(desc(TelemetryEvent.timestamp))
            .first()
        )
        latest_error_out = (
            TelemetryEventOut.from_orm(latest_error) if latest_error else None
        )
        
        return TelemetrySummary(
            total_events=total_events,
            events_by_severity=severity_counts,
            events_by_source=source_counts,
            events_by_category=category_counts,
            errors_last_hour=errors_last_hour,
            warnings_last_hour=warnings_last_hour,
            latest_error=latest_error_out,
        )
    
    def cleanup_old_events(self, older_than_days: int = 90) -> int:
        """
        Delete telemetry events older than specified days.
        
        Useful for managing database size and GDPR compliance.
        
        Args:
            older_than_days: Delete events older than this many days (default 90)
        
        Returns:
            Number of events deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        deleted = (
            self.db.query(TelemetryEvent)
            .filter(TelemetryEvent.timestamp < cutoff)
            .delete()
        )
        self.db.commit()
        return deleted


def get_telemetry_service(db: Session) -> TelemetryService:
    """Factory function to create TelemetryService instance."""
    return TelemetryService(db)
