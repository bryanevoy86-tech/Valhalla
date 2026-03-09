from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/monthly_close", tags=["core-monthly-close"])

@router.post("")
def close(month: str):
    try:
        return service.close(month=month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items():
    return {"items": service.list_items()}
