"""
Contracts router - manage templates, generate PDFs, and list/fetch records.
"""

import os
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..core.contract_render import render_text, make_pdf
from ..models.contracts import ContractTemplate, ContractRecord
from ..schemas.contracts import TemplateIn, TemplateOut, GenerateIn, RecordOut

router = APIRouter(prefix="/contracts", tags=["contracts"])

SAVE_DIR = os.getenv("CONTRACTS_DIR", "/tmp/contracts")


@router.post("/templates", response_model=TemplateOut)
def add_template(payload: TemplateIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    row = ContractTemplate(
        name=payload.name,
        version=payload.version,
        notes=payload.notes,
        body_text=payload.body_text,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/templates", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    return db.query(ContractTemplate).order_by(ContractTemplate.id.desc()).limit(200).all()


@router.post("/generate", response_model=RecordOut)
def generate_contract(payload: GenerateIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    tmpl = db.get(ContractTemplate, payload.template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="template not found")

    os.makedirs(SAVE_DIR, exist_ok=True)

    # support Jinja2 in filename too (e.g., assignment_{{deal_id}}.pdf)
    pdf_name = render_text(payload.filename, payload.data)
    if not pdf_name.endswith(".pdf"):
        pdf_name += ".pdf"
    path = os.path.join(SAVE_DIR, pdf_name)

    filled_text = render_text(tmpl.body_text, payload.data)
    pdf_bytes = make_pdf(filled_text)
    with open(path, "wb") as f:
        f.write(pdf_bytes)

    rec = ContractRecord(template_id=tmpl.id, filename=pdf_name, context_json=json.dumps(payload.data))
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return RecordOut(id=rec.id, filename=rec.filename, template_id=rec.template_id)


@router.get("/records", response_model=List[RecordOut])
def list_records(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    rows = db.query(ContractRecord).order_by(ContractRecord.id.desc()).limit(200).all()
    return [RecordOut(id=r.id, filename=r.filename, template_id=r.template_id) for r in rows]


@router.get("/records/{rec_id}/pdf")
def fetch_pdf(rec_id: int, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    row = db.get(ContractRecord, rec_id)
    if not row:
        raise HTTPException(status_code=404, detail="record not found")
    path = os.path.join(SAVE_DIR, row.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    with open(path, "rb") as f:
        b = f.read()
    return Response(content=b, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{row.filename}"'
    })
