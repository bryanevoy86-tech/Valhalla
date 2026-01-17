from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.db import get_db
from app.services.runbook import build_runbook, render_runbook_markdown

router = APIRouter(prefix="/governance/runbook", tags=["Governance", "Runbook"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    try:
        return build_runbook(db)
    except Exception as e:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "blockers": [{"id": "runbook_error", "ok": False, "severity": "BLOCKER", "message": "Runbook engine exception", "detail": {"error": str(e)}}],
            "warnings": [],
            "info": [],
            "ok_to_enable_go_live": False,
        }


@router.get("/markdown", response_class=PlainTextResponse)
def markdown(db: Session = Depends(get_db)):
    try:
        rb = build_runbook(db)
        return render_runbook_markdown(rb)
    except Exception as e:
        return f"# Runbook Error\n\nFailed to generate runbook: {str(e)}"

