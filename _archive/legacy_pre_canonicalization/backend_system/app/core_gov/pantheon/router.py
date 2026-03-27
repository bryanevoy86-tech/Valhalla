from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import ModeSetRequest, DispatchRequest, DispatchResponse, PantheonState
from . import service

router = APIRouter(prefix="/core/pantheon", tags=["core-pantheon"])


@router.get("/state", response_model=PantheonState)
def get_state():
    return service.get_state()


@router.post("/mode", response_model=PantheonState)
def set_mode(payload: ModeSetRequest):
    try:
        return service.set_mode(mode=payload.mode, reason=payload.reason, by="api")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dispatch", response_model=DispatchResponse)
def dispatch(payload: DispatchRequest):
    return service.dispatch(intent=payload.intent, payload=payload.payload, desired_band=payload.desired_band)
