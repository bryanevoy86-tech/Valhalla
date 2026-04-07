from __future__ import annotations

import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.contracts import (
    ContractCreateIn,
    ContractOut,
    ContractStateChangeIn,
    SendForSignatureIn,
    EventOut,
)
from app.services.contracts.service import ContractPipeline
from app.models.contracts import ContractEvent, ContractDocument

router = APIRouter(prefix="/api/contracts", tags=["Contracts"])


def _actor(request: Request) -> str:
    return request.headers.get("x-actor", "system")


@router.post("", response_model=ContractOut)
def create_contract(payload: ContractCreateIn, request: Request, db: Session = Depends(get_db)):
    try:
        svc = ContractPipeline(db)
        c = svc.create_contract(
            template_code=payload.template_code,
            title=payload.title,
            deal_id=payload.deal_id,
            zone_id=payload.zone_id,
            merge_data=payload.merge_data,
            parties=payload.parties,
            sign_provider=payload.sign_provider,
            actor=_actor(request),
        )
        return c
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/state", response_model=ContractOut)
def change_state(
    contract_id: str, payload: ContractStateChangeIn, request: Request, db: Session = Depends(get_db)
):
    try:
        svc = ContractPipeline(db)
        c = svc.change_state(contract_id, payload.target, _actor(request), payload.note)
        return c
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/upload")
async def upload_doc(
    contract_id: str,
    request: Request,
    kind: str = "DRAFT",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        data = await file.read()
        svc = ContractPipeline(db)
        doc = svc.upload_document(
            contract_id=contract_id,
            filename=file.filename or "upload.pdf",
            content_type=file.content_type or "application/pdf",
            kind=kind,
            data=data,
            actor=_actor(request),
        )
        return {"ok": True, "doc_id": doc.id, "filename": doc.filename, "kind": kind}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/send")
def send_for_signature(
    contract_id: str, payload: SendForSignatureIn, request: Request, db: Session = Depends(get_db)
):
    try:
        svc = ContractPipeline(db)
        env = svc.send_for_signature(contract_id, payload.subject, payload.message, _actor(request))
        return {
            "ok": True,
            "envelope_id": env.id,
            "provider_envelope_id": env.provider_envelope_id,
            "status": env.status,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{contract_id}/documents/{doc_id}/download")
def download_doc(contract_id: str, doc_id: str, db: Session = Depends(get_db)):
    """
    Download contract document.
    
    For S3 storage (production): returns presigned URL.
    For local storage (dev): returns document bytes.
    """
    doc = db.query(ContractDocument).filter(
        ContractDocument.id == doc_id,
        ContractDocument.contract_id == contract_id
    ).one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # If using S3 storage, return presigned URL (best for production)
    backend = os.getenv("CONTRACT_STORAGE_BACKEND", "s3").lower().strip()
    if backend == "s3":
        from app.services.contracts.storage_s3 import S3ContractStorage
        s3 = S3ContractStorage()
        url = s3.presign_get(doc.storage_key, expires_seconds=900)
        return {
            "ok": True,
            "url": url,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "expires_seconds": 900,
        }

    # Fallback: inline bytes (dev only)
    svc = ContractPipeline(db)
    data = svc.storage.get_bytes(doc.storage_key)
    return Response(content=data, media_type=doc.content_type)


@router.post("/templates/seed")
def seed_templates(db: Session = Depends(get_db)):
    """
    Seed default contract templates.
    
    Idempotent: only creates templates that don't already exist.
    """
    from app.services.contracts.seed_templates import seed_contract_templates
    return seed_contract_templates(db)


@router.get("/{contract_id}/events", response_model=list[EventOut])
def list_events(contract_id: str, db: Session = Depends(get_db)):
    events = (
        db.query(ContractEvent)
        .filter(ContractEvent.contract_id == contract_id)
        .order_by(ContractEvent.created_at.asc())
        .all()
    )
    return events
