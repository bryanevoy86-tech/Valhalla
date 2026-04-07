from fastapi import APIRouter
from app.core_eia.eia_report_generator import generate_monthly_report

router = APIRouter()

@router.get("/api/eia/monthly-report", tags=["EIA"])
def eia_monthly_report(month: str = None):
    return generate_monthly_report(month)
