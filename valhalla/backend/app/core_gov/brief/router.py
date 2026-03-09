"""
P-BRIEF-1: Brief API router.

GET /core/brief - Get system brief
"""
from fastapi import APIRouter
from typing import Dict, Any
from . import service

router = APIRouter(prefix="/core", tags=["brief"])


@router.get("/brief", response_model=Dict[str, Any])
async def get_brief() -> Dict[str, Any]:
    """
    Get a brief aggregating key information.
    
    Returns:
        Brief dict with mode, bills_upcoming, followups_open, cash_plan
    """
    return service.build()
