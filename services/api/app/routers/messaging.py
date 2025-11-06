"""
Messaging (Email/SMS) router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.messaging.service import MessagingService
from app.messaging.schemas import (
    EmailTemplateCreate, EmailTemplateOut,
    SendEmailRequest, SendSmsRequest, SendWithTemplateRequest,
    NotifyUserRequest
)

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
    svc = MessagingService(db)
    res = svc.send_email_raw(payload.to, payload.subject, payload.body, html=payload.html)
    if res.get("status") == "failure":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res


@router.post("/send-sms")
async def send_sms(payload: SendSmsRequest, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    res = svc.send_sms_raw(payload.to, payload.message)
    if res.get("status") == "failure":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res


@router.post("/send-with-template")
async def send_with_template(payload: SendWithTemplateRequest, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    res = svc.send_with_template(payload.template_name, payload.to, payload.user_id, payload.variables)
    if res.get("status") == "failure":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/notify-user")
async def notify_user(payload: NotifyUserRequest, db: Session = Depends(get_db)):
    svc = MessagingService(db)
    res = svc.notify_user_by_preferences(payload.user_id, payload.subject, payload.body, payload.sms_message)
    if res.get("status") == "failure":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res
