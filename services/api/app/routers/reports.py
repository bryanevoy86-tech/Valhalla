from fastapi import APIRouter

router = APIRouter()


@router.get("/reports/summary")
def get_reports_summary():
    """Get summary of reports"""
    return {"ok": True, "summary": {"total_reports": 0, "pending": 0, "completed": 0}}
