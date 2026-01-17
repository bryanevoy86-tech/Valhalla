from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from .schemas import PackCreate, PackListResponse, ValidateResponse
from . import service

router = APIRouter(prefix="/core/packs", tags=["core-packs"])


@router.post("")
def create(payload: PackCreate):
    try:
        return service.create_pack(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PackListResponse)
def list_all(tag: Optional[str] = None):
    return {"items": service.list_packs(tag=tag)}


@router.get("/validate", response_model=ValidateResponse)
def validate():
    return service.validate()
