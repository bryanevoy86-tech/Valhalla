"""P-BUDFLOW-1: Budget flow router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/core/budget_flow", tags=["budget_flow"])

class RunRequest(BaseModel):
    dry_run: bool = False

class RunResponse(BaseModel):
    done: bool
    warnings: list[str]
    followups_created: int
    board: dict

@router.post("/run")
def run_flow(req: RunRequest) -> RunResponse:
    """
    Execute the no-missed-payments flow.
    
    Orchestrates: obligations check → autopay verification → followup creation → ops board.
    """
    result = service.run()
    return RunResponse(**result)
