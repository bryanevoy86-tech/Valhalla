from __future__ import annotations

from fastapi import APIRouter

from .schemas import ShieldConfig, ShieldUpdate, EvaluateRequest, EvaluateResponse
from . import service

router = APIRouter(prefix="/core/shield", tags=["core-shield"])


@router.get("/config", response_model=ShieldConfig)
def get_config():
    return service.get_config()


@router.post("/config", response_model=ShieldConfig)
def update_config(payload: ShieldUpdate):
    return service.update_config(payload.model_dump())


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(payload: EvaluateRequest):
    return service.evaluate(
        reserves=float(payload.reserves or 0.0),
        pipeline_deals=int(payload.pipeline_deals or 0),
        override_tier=payload.override_tier,
    )
