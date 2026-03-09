from __future__ import annotations
from fastapi import APIRouter
from .service import board

router = APIRouter(prefix="/core/personal_board", tags=["core-personal-board"])

@router.get("")
def get():
    return board()
