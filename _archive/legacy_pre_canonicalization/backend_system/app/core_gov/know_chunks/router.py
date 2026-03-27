from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from . import service
from typing import Any, Dict

router = APIRouter(prefix="/core/know/chunks", tags=["core-know-chunks"])

@router.post("")
def chunk(source_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        return service.chunk_text(source_id=source_id, text=str((payload or {}).get("text","")), chunk_size=int((payload or {}).get("chunk_size",800)))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
