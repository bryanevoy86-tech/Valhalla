"""Generate and retrieve internal PDFs using canonical contract records."""

import hashlib
import re
from typing import List
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from jinja2 import TemplateError
from sqlalchemy.orm import Session

from app.core.contract_render import make_pdf, render_text
from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.contracts import Contract, ContractDocKind, ContractDocument, ContractTemplate, SignProvider
from app.schemas.contracts import GenerateIn, RecordOut, TemplateIn, TemplateOut
from app.services.contracts.service import ContractPipeline

router = APIRouter(prefix="/contracts", tags=["contracts"], dependencies=[Depends(require_builder_key)])

DOCUMENT_KEY = "valhalla_pdf_template"


def create_pdf_template(db: Session, payload: TemplateIn, *, metadata: dict | None = None) -> ContractTemplate:
    template_id = uuid4().hex
    template = ContractTemplate(
        id=template_id,
        code=f"pdf-{template_id}",
        name=payload.name,
        description=payload.notes,
        merge_schema={DOCUMENT_KEY: {
            "version": payload.version, "body_text": payload.body_text, **(metadata or {}),
        }},
    )
    db.add(template)
    db.commit()
    return template


def template_out(template: ContractTemplate) -> TemplateOut:
    pdf = template.merge_schema[DOCUMENT_KEY]
    return TemplateOut(
        id=template.id, name=template.name, notes=template.description,
        version=pdf["version"], body_text=pdf["body_text"],
    )


def _record_out(doc: ContractDocument, template_id: str) -> RecordOut:
    return RecordOut(id=doc.id, filename=doc.filename, template_id=template_id, created_at=doc.created_at)


def _render(template: ContractTemplate, filename: str, inputs: dict) -> tuple[str, bytes]:
    metadata = template.merge_schema.get(DOCUMENT_KEY)
    if metadata is None:
        raise HTTPException(status_code=409, detail="Template has no PDF rendering definition")
    try:
        name = render_text(filename, inputs)
        body = render_text(metadata["body_text"], inputs)
    except TemplateError:
        raise HTTPException(status_code=422, detail="Template rendering failed") from None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,180}", name):
        raise HTTPException(status_code=422, detail="Invalid PDF filename")
    name = name if name.endswith(".pdf") else f"{name}.pdf"
    return name, make_pdf(body)


@router.post("/templates", response_model=TemplateOut)
def add_template(payload: TemplateIn, db: Session = Depends(get_db)):
    return template_out(create_pdf_template(db, payload))


@router.get("/templates", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    rows = (
        db.query(ContractTemplate).filter(ContractTemplate.code.like("pdf-%"))
        .order_by(ContractTemplate.created_at.desc()).limit(200).all()
    )
    return [template_out(row) for row in rows if DOCUMENT_KEY in row.merge_schema]


@router.post("/generate", response_model=RecordOut)
def generate_contract(payload: GenerateIn, db: Session = Depends(get_db)):
    template = db.get(ContractTemplate, str(payload.template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    name, data = _render(template, payload.filename, payload.data)
    service = ContractPipeline(db)
    contract = service.create_contract(
        template.code, name, None, None, payload.data, [], SignProvider.SANDBOX, "builder", commit=False,
    )
    doc = service.upload_document(contract.id, name, "application/pdf", ContractDocKind.DRAFT, data, "builder")
    return _record_out(doc, template.id)


@router.get("/records", response_model=List[RecordOut])
def list_records(db: Session = Depends(get_db)):
    rows = (
        db.query(ContractDocument, Contract)
        .join(Contract, Contract.id == ContractDocument.contract_id)
        .join(ContractTemplate, ContractTemplate.id == Contract.template_id)
        .filter(ContractTemplate.code.like("pdf-%"), ContractDocument.kind == ContractDocKind.DRAFT)
        .order_by(ContractDocument.created_at.desc()).limit(200).all()
    )
    return [_record_out(doc, contract.template_id) for doc, contract in rows]


@router.get("/records/{rec_id}/pdf")
def fetch_pdf(rec_id: str, db: Session = Depends(get_db)):
    doc = db.get(ContractDocument, rec_id)
    contract = db.get(Contract, doc.contract_id) if doc else None
    template = db.get(ContractTemplate, contract.template_id) if contract else None
    if template is None or DOCUMENT_KEY not in template.merge_schema:
        raise HTTPException(status_code=404, detail="Record not found")
    try:
        data = ContractPipeline(db).storage.get_bytes(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF missing") from None
    if doc.sha256 != hashlib.sha256(data).hexdigest() or doc.bytes != len(data):
        raise HTTPException(status_code=409, detail="PDF failed integrity verification")
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(doc.filename, safe='')}"},
    )
