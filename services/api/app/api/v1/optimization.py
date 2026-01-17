# app/api/v1/optimization.py
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_admin_user
from app.heimdall.optimization_control import (
    OptimizationControlService,
    OptimizationSettings,
)

router = APIRouter(prefix="/optimization", tags=["optimization"])

@router.get("/settings", response_model=OptimizationSettings)
async def get_optimization_settings(user=Depends(get_current_admin_user)):
    """
    Read the current governance / evolution / shield settings.
    Heimdall will consult this before major decisions.
    """
    return await OptimizationControlService.get_settings()

@router.put("/settings", response_model=OptimizationSettings)
async def update_optimization_settings(
    payload: OptimizationSettings,
    user=Depends(get_current_admin_user),
):
    """
    Update master optimization switches.
    This is the 'Eternal Optimization Mode' control surface.
    """
    return await OptimizationControlService.update_settings(payload)
