"""
PACK TT: Security Dashboard Router
API endpoint for unified security dashboard view.
Aggregates data from rate limiting, security policies, and telemetry.
Marked as stable API (STABLE CONTRACT).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.db import get_db
from app.schemas.security_dashboard import SecurityDashboardSnapshot
from app.services import security_dashboard

router = APIRouter(prefix="/security", tags=["Security Dashboard"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get unified security dashboard with aggregated data from all security systems.
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Aggregates data from:
    - Rate limiting violations and rules
    - Security policies and blocked entities
    - Recent security events from telemetry
    - System health status
    
    Returns:
        Dict with aggregated security status including:
        - active_blocks: Number of currently blocked entities
        - violations_last_hour: Recent rate limit violations
        - policy_status: Current security policy settings
        - latest_alerts: Recent security events
        - overall_risk_level: Computed risk assessment
    
    Args:
        db: Database session (injected)
    
    Returns:
        Security dashboard snapshot with comprehensive security overview
    """
    result = await security_dashboard.get_security_dashboard(db)
    return result
