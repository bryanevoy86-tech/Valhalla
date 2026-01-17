"""System Health Endpoint Router"""
from fastapi import APIRouter

from .schemas import SystemHealthSummary
from .service import get_system_health

router = APIRouter(prefix="/system", tags=["system_health"])


@router.get("/health", response_model=SystemHealthSummary)
def system_health():
    """Get system health status - checks API, worker, email, database, and queue."""
    return get_system_health()
