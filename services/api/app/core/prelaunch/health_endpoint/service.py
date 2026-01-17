"""System Health Endpoint Service"""
from .schemas import (
    ServiceStatus,
    DatabaseStatus,
    QueueStatus,
    SystemHealthSummary,
)


def get_system_health() -> SystemHealthSummary:
    """
    Get system health status.
    
    Placeholder health implementation. Later:
    - ping DB
    - check worker/queue
    - check critical external services
    """

    services = [
        ServiceStatus(name="api", status="OK", latency_ms=30.0),
        ServiceStatus(name="worker", status="OK", latency_ms=None),
        ServiceStatus(name="email", status="OK", latency_ms=None),
    ]

    db_status = DatabaseStatus(status="OK", connections=None, slow_queries=None)
    queue_status = QueueStatus(status="OK", pending_jobs=0, failed_jobs=0)

    notes: list[str] = ["Health endpoint is using placeholder checks."]

    overall_status = "OK"

    return SystemHealthSummary(
        status=overall_status,
        services=services,
        db=db_status,
        queue=queue_status,
        notes=notes,
    )
