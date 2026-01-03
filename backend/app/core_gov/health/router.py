"""Health status endpoints - R/Y/G status for phone/dashboard."""
from fastapi import APIRouter

from .status import ryg_status

router = APIRouter(prefix="/status", tags=["Core: Status"])


@router.get("/ryg")
def status_ryg():
    """Get red/yellow/green status with detailed reasons."""
    return ryg_status()
