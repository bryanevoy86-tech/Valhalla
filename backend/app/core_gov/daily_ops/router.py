"""
P-DAILYOPS-1: Daily operations API router.

POST /core/daily_ops/run - Execute daily operations
"""
from fastapi import APIRouter
from typing import Dict, Any, Optional
from pydantic import BaseModel
from . import service

router = APIRouter(prefix="/core", tags=["daily_ops"])


class DailyOpsRequest(BaseModel):
    """Request model for daily operations."""
    days_bills: int = 7


@router.post("/daily_ops/run", response_model=Dict[str, Any])
async def run_daily_ops(req: DailyOpsRequest) -> Dict[str, Any]:
    """
    Execute daily operations.
    
    Args:
        req: Request with days_bills parameter
    
    Returns:
        Result dict with operation outcomes
    """
    return service.run(days_bills=req.days_bills)
