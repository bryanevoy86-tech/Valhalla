from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/mode", tags=["core-mode"])

@router.get("")
def get_mode():
    return service.get()

@router.post("")
def set_mode(mode: str, reason: str = ""):
    try:
        return service.set(mode=mode, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
