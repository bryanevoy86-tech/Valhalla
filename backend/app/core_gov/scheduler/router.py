"""
P-SCHED-1: Scheduler API router.

GET /core/scheduler/state - Get scheduler state
POST /core/scheduler/tick - Execute scheduler tick
"""
from fastapi import APIRouter
from typing import Dict, Any
from . import service, store

router = APIRouter(prefix="/core", tags=["scheduler"])


@router.get("/scheduler/state", response_model=Dict[str, Any])
async def get_scheduler_state() -> Dict[str, Any]:
    """
    Get current scheduler state.
    
    Returns:
        State dict with last_tick, next_tick, enabled
    """
    return store.get_state()


@router.post("/scheduler/tick", response_model=Dict[str, Any])
async def execute_tick() -> Dict[str, Any]:
    """
    Execute a scheduler tick (periodic operations).
    
    Returns:
        Tick result with tick_id, timestamp, daily_ops_result
    """
    return service.tick()
