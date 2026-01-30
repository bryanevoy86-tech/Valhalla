"""
Notification Router - Send test and operational emails.

Endpoints:
  POST /api/notify/test-email       - Test email to verify notification channel
  POST /api/notify/daily-ops-email  - Send real daily ops summary email

Authentication:
  Both endpoints can be called without authentication by default.
  If VALHALLA_CRON_TOKEN is set in environment, cron jobs can use:
    - Header: Authorization: Bearer {VALHALLA_CRON_TOKEN}
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.identity import system_identity
from app.core.db import get_db
from app.services.email_service import send_email
from app.jobs.daily_ops_email import build_daily_ops_body

router = APIRouter(prefix="/notify", tags=["notify"])


def _verify_cron_token(authorization: str | None = Header(None)) -> bool:
    """
    Verify cron token if it's configured.
    
    If VALHALLA_CRON_TOKEN is set, requires valid token in Authorization header.
    If not set, allows unauthenticated access.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        bool: True if token is valid or not required
        
    Raises:
        HTTPException: If token is required but missing or invalid
    """
    cron_token = os.getenv("VALHALLA_CRON_TOKEN", "").strip()
    
    # If no cron token configured, allow unauthenticated access
    if not cron_token:
        return True
    
    # If cron token is configured, require it
    if not authorization:
        raise HTTPException(
            status_code=403,
            detail="VALHALLA_CRON_TOKEN is configured; Authorization header required"
        )
    
    # Extract bearer token
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Invalid Authorization header format. Use: Bearer {token}"
        )
    
    # Verify token
    if token != cron_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired VALHALLA_CRON_TOKEN"
        )
    
    return True


@router.post("/test-email")
def test_email(auth: bool = Depends(_verify_cron_token)):
    """
    Send a test email from the system account.
    
    This endpoint verifies that:
    1. System identity is configured (VALHALLA_SYSTEM_EMAIL)
    2. Email service can send messages
    3. Notification channel is online
    
    Returns:
        dict: Status of the test email send
    """
    identity = system_identity()
    to_email = identity["email"]

    send_email(
        to_email=to_email,
        subject="Heimdall: Notification channel online ✅",
        body="If you received this, Valhalla can send operational emails from Render."
    )
    
    return {
        "ok": True,
        "sent_to": to_email,
        "subject": "Heimdall: Notification channel online ✅"
    }


@router.post("/daily-ops-email")
def daily_ops_email(
    db: Session = Depends(get_db),
    auth: bool = Depends(_verify_cron_token)
):
    """
    Send the real daily ops email to system inbox.
    
    Builds a comprehensive daily operations summary with:
    - System health and dependencies
    - Runbook status, blockers, warnings
    - Deal pipeline (counts by stage)
    - Top tasks due today
    - Outcomes/results from yesterday
    - Links to governance, runbook, API health
    
    Authentication:
    - If VALHALLA_CRON_TOKEN is set, requires: Authorization: Bearer {token}
    - Otherwise, no authentication required
    
    Returns:
        dict: Status of the email send with summary metrics
    """
    identity = system_identity()
    to_email = identity["email"]
    
    # Build comprehensive email body
    body = build_daily_ops_body(db)
    
    # Extract summary metrics from the body for return value
    subject = "Heimdall: Daily Ops (9AM)"
    
    # Send the email
    success = send_email(
        to_email=to_email,
        subject=subject,
        body=body,
    )
    
    from datetime import datetime, timezone
    
    return {
        "ok": success,
        "sent_to": to_email,
        "subject": subject,
        "summary": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "body_length": len(body),
            "sections": [
                "header",
                "health_status",
                "runbook_status",
                "deal_pipeline",
                "todays_tasks",
                "yesterdays_results",
                "quick_links"
            ]
        }
    }
