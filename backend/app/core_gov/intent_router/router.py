from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/intent", tags=["core-intent"])

@router.post("")
def intent(payload: Dict[str, Any] = Body(...)):
    try:
        return service.handle_intent(intent=payload.get("intent",""), payload=payload.get("payload") or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
