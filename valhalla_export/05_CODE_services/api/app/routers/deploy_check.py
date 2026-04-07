# services/api/app/routers/deploy_check.py

"""
Deployment Check Router for PACK V: Deployment Checklist / Ops Automation
Provides pre-deploy sanity check endpoint for operational readiness.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.deploy_check import deploy_check
from app.schemas.deploy_check import DeploymentCheckResult

router = APIRouter(prefix="/ops/deploy-check", tags=["Ops", "Deployment"])


@router.get("/", response_model=DeploymentCheckResult, summary="Run deployment readiness check")
def run_deploy_check(request: Request, db: Session = Depends(get_db)):
    """
    Run comprehensive deployment readiness check.
    
    Verifies:
    - All required environment variables are set
    - Database is reachable and healthy
    - Critical API routes are registered
    
    Returns overall_ok: true only if ALL checks pass.
    Use this endpoint before deploying to a new environment or scaling.
    
    Response includes detailed breakdown of each check for debugging.
    """
    app = request.app
    return deploy_check(app, db)
