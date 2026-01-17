from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Body
from . import service

router = APIRouter(prefix="/core/exports", tags=["core-exports"])

@router.post("/bundle")
def bundle(payload: Dict[str, Any] = Body(...)):
    keys = payload.get("keys") or []
    return service.export_bundle(keys=keys)
