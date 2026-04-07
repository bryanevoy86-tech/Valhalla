from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.legal.document_engine import TemplateNotFoundError, list_templates
from app.legal.legal_send_service import approve_queued_send, queue_legal_document
from app.legal.approval_send_orchestrator import approve_and_send_legal_document
from app.legal.queue_reader import get_queue_item
from app.legal.deal_stage_triggers import get_stage_template_map, queue_legal_for_stage
from app.legal.recipient_registry import (
    get_registry,
    resolve_legal_contacts,
    update_company_region_contacts,
)
from app.legal.document_package_builder import (
    get_stage_package_map,
    queue_legal_package_for_stage,
)
from app.legal.package_send_orchestrator import approve_and_send_package
from app.legal.document_status_feed import (
    get_document_status_summary,
    get_document_status_feed,
    get_package_history,
    get_audit_event_feed,
)

router = APIRouter(prefix="/api/legal", tags=["Legal"])


class QueueLegalRequest(BaseModel):
    approval_id: str = Field(..., description="Unique approval/job id")
    template_key: str
    payload: dict
    recipients: list[str]
    cc: list[str] = []
    body_intro: str | None = None


class StageTriggerRequest(BaseModel):
    stage: str
    deal: dict


class RegistryUpdateRequest(BaseModel):
    company_name: str
    region_code: str
    lawyer_email: str = ""
    accountant_email: str = ""
    title_company: str = ""
    title_company_email: str = ""
    cc: list[str] = []


class PackageSendRequest(BaseModel):
    stage: str
    deal_id: str


@router.get("/templates")
def get_legal_templates():
    return {"templates": list_templates()}


@router.get("/stage-map")
def get_legal_stage_map():
    return {"stage_template_map": get_stage_template_map()}


@router.get("/package-map")
def get_legal_package_map():
    return {"stage_package_map": get_stage_package_map()}


@router.get("/registry")
def get_legal_registry():
    return get_registry()


@router.get("/registry/resolve")
def resolve_legal_registry(company_name: str = "", region_code: str = "", deal_type: str = ""):
    return resolve_legal_contacts(company_name=company_name, region_code=region_code, deal_type=deal_type)


@router.post("/registry/update-region")
def update_legal_registry_region(req: RegistryUpdateRequest):
    return update_company_region_contacts(
        company_name=req.company_name,
        region_code=req.region_code,
        lawyer_email=req.lawyer_email,
        accountant_email=req.accountant_email,
        title_company=req.title_company,
        title_company_email=req.title_company_email,
        cc=req.cc,
    )


@router.get("/status/summary")
def get_legal_status_summary():
    return get_document_status_summary()


@router.get("/status/feed")
def get_legal_status_feed(limit: int = 100):
    return get_document_status_feed(limit=limit)


@router.get("/status/packages")
def get_legal_package_history(limit: int = 100):
    return get_package_history(limit=limit)


@router.get("/status/audit")
def get_legal_audit_feed(limit: int = 200):
    return get_audit_event_feed(limit=limit)


@router.post("/queue")
def queue_legal_doc(req: QueueLegalRequest):
    try:
        return queue_legal_document(
            approval_id=req.approval_id,
            template_key=req.template_key,
            payload=req.payload,
            recipients=req.recipients,
            cc=req.cc,
            body_intro=req.body_intro,
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/queue/{approval_id}")
def get_queued_legal_doc(approval_id: str):
    try:
        return get_queue_item(approval_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/approve/{approval_id}")
def approve_legal_doc(approval_id: str):
    try:
        return approve_queued_send(approval_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/approve-and-send/{approval_id}")
def approve_and_send_legal_doc(approval_id: str):
    try:
        result = approve_and_send_legal_document(approval_id)
        if result.get("approved") is False and result.get("sent") is False and result.get("reason"):
            raise HTTPException(status_code=400, detail=result)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/trigger-from-stage")
def trigger_legal_from_stage(req: StageTriggerRequest):
    result = queue_legal_for_stage(req.stage, req.deal)
    if not result.triggered and result.reason:
        raise HTTPException(status_code=400, detail=result.__dict__)
    return result.__dict__


@router.post("/trigger-package-from-stage")
def trigger_legal_package_from_stage(req: StageTriggerRequest):
    result = queue_legal_package_for_stage(req.stage, req.deal)
    if not result.triggered and result.reason:
        raise HTTPException(status_code=400, detail=result.__dict__)
    return result.__dict__


@router.post("/approve-and-send-package")
def approve_and_send_legal_package(req: PackageSendRequest):
    result = approve_and_send_package(stage=req.stage, deal_id=req.deal_id)
    if result.get("package_sent") is False and result.get("reason"):
        raise HTTPException(status_code=400, detail=result)
    return result
