"""Trajectory Engine Router"""
from fastapi import APIRouter
from .schemas import CurrentTrajectory, ScenarioRequest, ScenarioResult
from .service import get_current_trajectory, simulate_scenario

router = APIRouter(prefix="/trajectory", tags=["trajectory"])


@router.get("/current", response_model=CurrentTrajectory)
def current():
    """Get current financial trajectory projection."""
    return get_current_trajectory()


@router.post("/scenario", response_model=ScenarioResult)
def scenario(payload: ScenarioRequest):
    """Simulate a 'what if' scenario with deal/bankroll/expense adjustments."""
    return simulate_scenario(payload)
