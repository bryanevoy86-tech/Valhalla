from fastapi import APIRouter
from app.core_gov.reality.weekly_service import run_weekly_audit
from app.core_gov.reality.weekly_store import load_audits

router = APIRouter(prefix="/reality", tags=["Core: Reality"])


@router.post("/weekly_audit")
def weekly_audit():
    return run_weekly_audit()


@router.get("/weekly_audits")
def weekly_audits(limit: int = 20):
    items = load_audits()
    return {"items": items[-limit:][::-1]}
