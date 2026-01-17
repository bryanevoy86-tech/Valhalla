"""P-TAXREP-1: Tax report router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/core/tax", tags=["tax"])

class ReportResponse(BaseModel):
    month: str
    by_bucket: dict[str, float]
    unmapped: list[dict]

@router.get("/report/{month}")
def get_report(month: str) -> ReportResponse:
    """Get tax summary report for a month (YYYY-MM)."""
    report = service.summary(month)
    return ReportResponse(**report)
