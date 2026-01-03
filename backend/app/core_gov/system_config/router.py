"""
P-SYSCFG-1: System configuration API router.

GET /core/system_config - Get current config
POST /core/system_config - Update config
"""
from fastapi import APIRouter
from typing import Dict, Any
from pydantic import BaseModel
from . import store

router = APIRouter(prefix="/core", tags=["system_config"])


class SystemConfig(BaseModel):
    """System configuration model."""
    soft_launch: bool = True
    require_approvals_for_execute: bool = False
    allow_external_sending: bool = False
    default_currency: str = "USD"


class SystemConfigPatch(BaseModel):
    """Patch for system configuration."""
    soft_launch: bool = None
    require_approvals_for_execute: bool = None
    allow_external_sending: bool = None
    default_currency: str = None


@router.get("/system_config", response_model=Dict[str, Any])
async def get_system_config() -> Dict[str, Any]:
    """
    Get current system configuration.
    
    Returns:
        Current configuration dict
    """
    return store.get()


@router.post("/system_config", response_model=Dict[str, Any])
async def patch_system_config(patch: SystemConfigPatch) -> Dict[str, Any]:
    """
    Update system configuration.
    
    Args:
        patch: Configuration changes
    
    Returns:
        Updated configuration dict
    """
    # Filter out None values
    patch_dict = {k: v for k, v in patch.dict().items() if v is not None}
    return store.save(patch_dict)
