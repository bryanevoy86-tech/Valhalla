from __future__ import annotations

from fastapi import APIRouter, Query

from .schemas import WeeklyCheckResponse
from . import service

router = APIRouter(prefix="/core/weekly", tags=["core-weekly"])


@router.post("/run", response_model=WeeklyCheckResponse)
def run(create_followups: bool = Query(default=True)):
    return service.run_weekly(create_followups=create_followups)
