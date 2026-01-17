from fastapi import APIRouter
from app.core_gov.deals.summary_service import deals_summary

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

@router.get("/summary")
def summary(limit_scan: int = 3000, top_n: int = 15):
    return deals_summary(limit_scan=limit_scan, top_n=top_n)
