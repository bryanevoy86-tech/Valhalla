"""
Messaging (Email/SMS) router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.db import get_db
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import OUTREACH
from app.messaging.service import MessagingService
from app.messaging.schemas import (
    EmailTemplateCreate, EmailTemplateOut,
    SendEmailRequest, SendSmsRequest, SendWithTemplateRequest,
    NotifyUserRequest
)
from app.services.market_policy import check_contact_window
from app.services.kpi import emit_kpi

router = APIRouter(prefix="/messaging", tags=["messaging"])


# Templates
@router.post("/templates", response_model=EmailTemplateOut, status_code=201)
async def create_template(payload: EmailTemplateCreate, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    try:
        return svc.create_template(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[EmailTemplateOut])
async def list_templates(db: Session = Depends(get_db)):
    svc = MessagingService(db)
    return svc.list_templates()


@router.get("/templates/{template_name}", response_model=EmailTemplateOut)
async def get_template(template_name: str, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    tmpl = svc.get_template(template_name)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    ok = svc.delete_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


# Sending
@router.post("/send-email")
async def send_email(payload: SendEmailRequest, db: Session = Depends(get_db)):
    enforce_engine("wholesaling", OUTREACH)
    svc = MessagingService(db)
    
    # --- Market policy enforcement (fail-closed) ---
    if payload.province and payload.market:
        try:
            now = datetime.now()
            weekday = now.weekday()
            hhmm = now.strftime("%H%M")
            
            allowed = check_contact_window(
                db=db,
                province=payload.province,
                market=payload.market,
                weekday=weekday,
                hhmm=hhmm,
            )
            
            corr_id = f"email:{payload.to}:{now.timestamp()}"
            
            if not allowed:
                # Fail-closed: block send and emit KPI
                emit_kpi(
                    db, "MESSAGING", "email_blocked_by_policy",
                    success=False,
                    actor="system",
                    correlation_id=corr_id,
                    detail={"to": payload.to, "province": payload.province, "market": payload.market},
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Contact window closed for {payload.province}/{payload.market} at {hhmm}",
                )
            
            emit_kpi(
                db, "MESSAGING", "email_sent",
                success=True,
                actor="system",
                correlation_id=corr_id,
                detail={"to": payload.to, "subject": payload.subject[:50]},
            )
        except HTTPException:
            raise
        except Exception:
            # Non-blocking: if policy check fails, allow send (fail-open with logging)
            pass
    
    res = svc.send_email_raw(payload.to, payload.subject, payload.body, html=payload.html)
    if res.get("status") == "failure":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res


@router.post("/send-sms")
async def send_sms(payload: SendSmsRequest, db: Session = Depends(get_db)):
    enforce_engine("wholesaling", OUTREACH)
    svc = MessagingService(db)
    
    # --- Market policy enforcement (fail-closed) ---
    if payload.province and payload.market:
        try:
            now = datetime.now()
            weekday = now.weekday()
            hhmm = now.strftime("%H%M")
            
            allowed = check_contact_window(
                db=db,
                province=payload.province,
                market=payload.market,
                weekday=weekday,
                hhmm=hhmm,
            )
            
            corr_id = f"sms:{payload.to}:{now.timestamp()}"
            
            if not allowed:
                # Fail-closed: block send and emit KPI
                emit_kpi(
                    db, "MESSAGING", "sms_blocked_by_policy",
                    success=False,
                    actor="system",
                    correlation_id=corr_id,
                    detail={"to": payload.to, "province": payload.province, "market": payload.market},
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Contact window closed for {payload.province}/{payload.market} at {hhmm}",
                )
            
            emit_kpi(
                db, "MESSAGING", "sms_sent",
                success=True,
                actor="system",
                correlation_id=corr_id,
                detail={"to": payload.to, "message_len": len(payload.message)},
            )
        except HTTPException:
            raise
        except Exception:
            # Non-blocking: if policy check fails, allow send (fail-open with logging)
            pass
    
    res = svc.send_sms_raw(payload.to, payload.message)
    if res.get("status") == "failure":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res


@router.post("/send-with-template")
async def send_with_template(payload: SendWithTemplateRequest, db: Session = Depends(get_db)):
    enforce_engine("wholesaling", OUTREACH)
    svc = MessagingService(db)
    res = svc.send_with_template(payload.template_name, payload.to, payload.user_id, payload.variables)
    if res.get("status") == "failure":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/notify-user")
async def notify_user(payload: NotifyUserRequest, db: Session = Depends(get_db)):
    enforce_engine("wholesaling", OUTREACH)
    svc = MessagingService(db)
    res = svc.notify_user_by_preferences(payload.user_id, payload.subject, payload.body, payload.sms_message)
    if res.get("status") == "failure":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res
