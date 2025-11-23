# app/api/v1/diagnostics.py
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_admin_user
from app.diagnostics.engine import DiagnosticsEngine, DiagnosticSummary

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.get("/scan", response_model=DiagnosticSummary)
async def run_scan(user=Depends(get_current_admin_user)):
    return await DiagnosticsEngine.run()
