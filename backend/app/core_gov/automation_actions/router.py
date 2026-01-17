from __future__ import annotations

from fastapi import APIRouter
from .schemas import GenerateFollowupsRequest, GenerateFollowupsResponse
from . import service

router = APIRouter(prefix="/core/automation_actions", tags=["core-automation-actions"])


@router.post("/generate_followups", response_model=GenerateFollowupsResponse)
def generate(payload: GenerateFollowupsRequest):
    r = service.generate_followups(
        lookahead_days=payload.lookahead_days,
        dedupe_days=payload.dedupe_days,
        max_create=payload.max_create,
        mode=payload.mode,
        meta=payload.meta,
    )
    return r
