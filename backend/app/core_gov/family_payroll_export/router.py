from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/family_payroll_export", tags=["core-family-payroll-export"])

@router.get("/year_summary")
def year_summary(year: int):
    if not year:
        raise HTTPException(status_code=400, detail="year required")
    return service.year_summary(year=year)

@router.get("/entries_csv")
def entries_csv(year: int):
    if not year:
        raise HTTPException(status_code=400, detail="year required")
    return service.export_entries_csv(year=year)
