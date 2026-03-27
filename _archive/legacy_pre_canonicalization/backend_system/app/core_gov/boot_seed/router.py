"""
P-BOOT-1: Boot seed API router.

POST /core/boot/seed_minimum - Initialize minimum system data
"""
from fastapi import APIRouter
from typing import Dict, Any
from . import service

router = APIRouter(prefix="/core", tags=["boot"])


@router.post("/boot/seed_minimum", response_model=Dict[str, Any])
async def seed_minimum() -> Dict[str, Any]:
    """
    Initialize minimum required system data.
    
    Returns:
        Seed result with system_config, budget_categories, house_budget
    """
    return service.seed_minimum()
