"""P-OPSBOARD-1: Operations board router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/core/ops_board", tags=["ops_board"])

class BoardResponse(BaseModel):
    bills_due: list[dict]
    autopay_gaps: list[dict]
    inventory_low: list[dict]
    reminders: list[dict]
    outbox_ready: list[dict]

@router.get("")
def get_board() -> BoardResponse:
    """Get unified operations board for today."""
    board = service.today()
    return BoardResponse(**board)
