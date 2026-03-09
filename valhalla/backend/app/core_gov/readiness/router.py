"""
P-READINESS-1: Readiness API router.

GET /core/readiness - Check system readiness
"""
from fastapi import APIRouter
from typing import Dict, Any
from . import service

router = APIRouter(prefix="/core", tags=["readiness"])


@router.get("/readiness", response_model=Dict[str, Any])
async def get_readiness() -> Dict[str, Any]:
    """
    Check readiness status of all core modules.
    
    Returns:
        Readiness status dict with module checks and overall ready flag
    """
    return service.readiness()
