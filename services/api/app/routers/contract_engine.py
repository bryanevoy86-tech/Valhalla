"""Compatibility endpoints for the canonical contract workflow."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.contracts import Contract, ContractDocKind, ContractPartyRole, ContractState, ContractTemplate, SignProvider
from app.routers.contracts import DOCUMENT_KEY, _render, create_pdf_template
from app.routers.contracts_webhooks import provider_webhook
from app.schemas.contracts import PartyIn, TemplateIn as PdfTemplateIn
from app.services.contracts.service import ContractPipeline

router = APIRouter(prefix="/contract", tags=["contract"], dependencies=[Depends(require_prime_control_key)])


class TemplateIn(BaseModel):
    name: str
    jurisdiction: str
    language: str = "en"
    structure: list[str]


class ContractCreate(BaseModel):
    deal_id: int
    template_id: str | int
    variables: dict[str, Any]
    counterparty_email: EmailStr
    counterparty_name: str


@router.post("/template")
def create_template(payload: TemplateIn, db: Session = Depends(get_db)):
    template = create_pdf_template(
        db, PdfTemplateIn(name=payload.name, body_text="\n".join(payload.structure)),
        metadata=payload.model_dump(include={"jurisdiction", "language", "structure"}),
    )
    return {"ok": True, "template_id": template.id}


@router.get("/template/list")
def list_templates(jurisdiction: str | None = None, db: Session = Depends(get_db)):
    templates = []
    for row in db.query(ContractTemplate).filter(ContractTemplate.code.like("pdf-%")):
        pdf = row.merge_schema.get(DOCUMENT_KEY, {})
        if "jurisdiction" in pdf and (jurisdiction is None or pdf["jurisdiction"] == jurisdiction):
            templates.append({"id": row.id, "name": row.name, **pdf})
    return {"templates": templates}


def _contract(db: Session, contract_id: str) -> Contract:
    row = db.get(Contract, contract_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return row


@router.post("/draft")
def draft_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    template = db.get(ContractTemplate, str(payload.template_id))
    if template is None or DOCUMENT_KEY not in template.merge_schema:
        raise HTTPException(status_code=404, detail="Template not found")
    party = PartyIn(role=ContractPartyRole.OTHER, name=payload.counterparty_name, email=payload.counterparty_email)
    row = ContractPipeline(db).create_contract(
        template.code, template.name, str(payload.deal_id), None, payload.variables, [party], SignProvider.SANDBOX, "prime",
    )
    return {"ok": True, "contract_id": row.id, "status": row.state.value.lower()}


@router.post("/pdf/{contract_id}")
def build_pdf(contract_id: str, db: Session = Depends(get_db)):
    contract = _contract(db, contract_id)
    template = db.get(ContractTemplate, contract.template_id)
    if template is None:
        raise HTTPException(status_code=409, detail="Template unavailable")
    filename, data = _render(template, f"contract-{uuid4().hex}.pdf", contract.merge_data)
    doc = ContractPipeline(db).upload_document(
        contract.id, filename, "application/pdf", ContractDocKind.DRAFT, data, "prime",
    )
    return {"ok": True, "pdf_url": f"/api/contracts/records/{doc.id}/pdf", "sha256": doc.sha256}


@router.post("/send/{contract_id}")
def send_for_esign(contract_id: str, db: Session = Depends(get_db)):
    if _contract(db, contract_id).state != ContractState.APPROVED_FOR_SIGNATURE:
        raise HTTPException(status_code=409, detail="Contract requires signature approval")
    try:
        envelope = ContractPipeline(db).send_for_signature(contract_id, "Signature request", "Please review.", "prime")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"ok": True, "status": envelope.status, "envelope_id": envelope.id}


@router.get("/status/{contract_id}")
def contract_status(contract_id: str, db: Session = Depends(get_db)):
    row = _contract(db, contract_id)
    return {
        "contract_id": row.id, "status": row.state.value.lower(),
        "signers": [{"name": party.name, "signed_at": party.signed_at} for party in row.parties],
    }


@router.post("/webhook/esign")
async def esign_webhook(request: Request, db: Session = Depends(get_db)):
    return await provider_webhook(request, db)
