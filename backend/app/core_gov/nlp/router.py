from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict
from .service import parse
from .intent import intent

router = APIRouter(prefix="/core/nlp", tags=["core-nlp"])

@router.post("/parse")
def parse_ep(payload: Dict[str, Any] = Body(...)):
    text = str((payload or {}).get("text") or "")
    out = parse(text=text)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error"))
    return out

@router.post("/intent")
def intent_ep(payload: Dict[str, Any] = Body(...)):
    text = str((payload or {}).get("text") or "")
    out = intent(text=text)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error"))
    return out
