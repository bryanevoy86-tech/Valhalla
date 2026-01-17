"""
PACK TX: System Health & Kubernetes Readiness Router
Provides liveness, readiness, and metrics endpoints for system observability.
Marked as stable API (STABLE CONTRACT).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.system_health import HealthStatus, ReadinessStatus, BasicMetrics
from app.services.system_health import (
    get_health_status,
    get_readiness_status,
    get_basic_metrics,
)


router = APIRouter(prefix="/system-health", tags=["health"])


@router.get("/live", response_model=HealthStatus)
def liveness_probe() -> HealthStatus:
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if the application is running and responsive. This is used by
    orchestration platforms (Kubernetes, Docker Swarm, etc.) to determine if
    the pod/container should be restarted.
    
    **STABLE CONTRACT:** This endpoint path and format will not change.
    
    Returns:
        HealthStatus: Liveness probe result with status and timestamp
    """
    data = get_health_status()
    return HealthStatus(**data)


@router.get("/ready", response_model=ReadinessStatus)
def readiness_probe(db: Session = Depends(get_db)) -> ReadinessStatus:
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if the application is ready to accept requests. This checks:
    - Database connectivity and query capability
    - Essential dependencies are available
    
    Used by load balancers to route traffic to healthy instances.
    
    **STABLE CONTRACT:** This endpoint path and format will not change.
    
    Args:
        db: Database session (injected)
    
    Returns:
        ReadinessStatus: Readiness probe result with DB status and timestamp
    """
    data = get_readiness_status(db)
    return ReadinessStatus(**data)


@router.get("/metrics", response_model=BasicMetrics)
def metrics_endpoint() -> BasicMetrics:
    """
    Get basic application metrics (uptime, request rate hint, etc).
    
    Returns lightweight metrics suitable for dashboard display and monitoring.
    Can be extended in the future to include more detailed metrics.
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Returns:
        BasicMetrics: Current uptime and metric data
    """
    data = get_basic_metrics()
    return BasicMetrics(**data)
