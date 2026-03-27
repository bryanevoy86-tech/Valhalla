from __future__ import annotations

from fastapi import APIRouter
from .schemas import RiskAssessRequest, RiskAssessResponse
from . import service

router = APIRouter(prefix="/core/taxrisk", tags=["core-taxrisk"])


@router.post("/assess", response_model=RiskAssessResponse)
def assess(payload: RiskAssessRequest):
    r = service.assess(category=payload.category, tags=payload.tags, vendor=payload.vendor, notes=payload.notes)
    return r
