from fastapi import APIRouter

from app.health.service import HealthCheckService
from app.health.schemas import HealthCheckOut


router = APIRouter(prefix="/system-health", tags=["health"]) 


@router.get("", response_model=HealthCheckOut)
async def get_system_health():
    """Run health checks and return composite system status."""
    return HealthCheckService.check_system_health()
