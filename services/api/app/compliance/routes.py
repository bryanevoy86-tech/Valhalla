from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.compliance.eia_mode_controller import (
    get_compliance_mode_state,
    set_compliance_mode,
)
from app.compliance.eia_exit_handoff import (
    validate_eia_exit_handoff,
    execute_eia_exit_handoff,
)
from app.compliance.eia_audit_log import write_eia_audit

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


class ModeSwitchRequest(BaseModel):
    mode: str
    updated_by: str


class ExitHandoffRequest(BaseModel):
    audit_selfcheck_passed: bool
    reserve_floor_met: bool
    founder_approved: bool
    accountant_review_ready: bool
    updated_by: str = "manual_exit"


@router.get("/mode")
def get_mode():
    return get_compliance_mode_state()


@router.post("/mode")
def switch_mode(req: ModeSwitchRequest):
    state = set_compliance_mode(req.mode, req.updated_by)
    write_eia_audit("mode_switched", state)
    return state


@router.post("/eia/exit/validate")
def validate_eia_exit(req: ExitHandoffRequest):
    result = validate_eia_exit_handoff(req.model_dump())
    write_eia_audit("exit_validated", result)
    return result


@router.post("/eia/exit/execute")
def execute_eia_exit(req: ExitHandoffRequest):
    result = execute_eia_exit_handoff(req.model_dump())
    write_eia_audit("exit_executed", result)
    return result
