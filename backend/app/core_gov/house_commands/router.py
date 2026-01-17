"""P-HOUSECMD-1: Household command router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/core/house", tags=["house_commands"])

class CommandRequest(BaseModel):
    text: str

class CommandResponse(BaseModel):
    intent: str
    text: str
    action: dict

@router.post("/command")
def execute_command(req: CommandRequest) -> CommandResponse:
    """Parse and execute a household voice/text command."""
    result = service.execute(req.text)
    return CommandResponse(**result)
