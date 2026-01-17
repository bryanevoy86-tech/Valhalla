# app/api/v1/security.py
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_admin_user
from app.security.hardening import SecurityHardeningService, SecuritySummary

router = APIRouter(prefix="/security", tags=["security"])

@router.get("/summary", response_model=SecuritySummary)
async def get_security_summary(user=Depends(get_current_admin_user)):
    """
    Lightweight security posture summary.
    Heimdall will later plug in real scanners and checks here.
    """
    return await SecurityHardeningService.run_checks()
