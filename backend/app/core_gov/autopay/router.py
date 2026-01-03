from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import AutopayPlanRequest, AutopayPlanResponse
from . import service

router = APIRouter(prefix="/core/autopay", tags=["core-autopay"])


@router.post("/plan", response_model=AutopayPlanResponse)
def plan(payload: AutopayPlanRequest):
    try:
        return service.build_autopay_plan(
            obligation_id=payload.obligation_id,
            bank=payload.bank,
            mode=payload.mode,
            meta=payload.meta,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")
