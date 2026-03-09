from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Body
from . import service

router = APIRouter(prefix="/core/text_commands", tags=["core-text-commands"])

@router.post("/parse")
def parse(payload: Dict[str, Any] = Body(...)):
    return service.parse(text=payload.get("text",""))
