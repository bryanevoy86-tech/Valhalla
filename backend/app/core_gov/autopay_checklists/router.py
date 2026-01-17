from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/autopay", tags=["core-autopay"])

@router.get("/checklist/{obligation_id}")
def checklist(obligation_id: str):
    try:
        return service.build_for_obligation(obligation_id=obligation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
