from __future__ import annotations
from fastapi import APIRouter
from .service import board
from .outbox_updates import create_updates

router = APIRouter(prefix="/core/jv_board", tags=["core-jv-board"])

@router.get("")
def get():
    return board()

@router.post("/outbox_update")
def outbox_update(to: str = "(paste)", channel: str = "email"):
    return create_updates(to=to, channel=channel)
