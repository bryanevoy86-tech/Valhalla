"""
Pack 51: Legal Document Engine - API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import CONTRACT_SEND
from app.legal.schemas import *
from app.legal import service as svc
from app.legal.models import LegalTemplate, LegalTemplateVersion, LegalClause, LegalVariable, LegalDocument

router = APIRouter(prefix="/legal", tags=["legal"])


@router.post("/templates", response_model=TemplateOut)
def create_template(body: TemplateIn, db: Session = Depends(get_db)):
    t = svc.upsert_template(db, body.model_dump())
    return TemplateOut.model_validate(t)


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    rows = db.query(LegalTemplate).order_by(LegalTemplate.name.asc()).all()
    return [TemplateOut.model_validate(r) for r in rows]


@router.post("/versions")
def create_version(body: VersionIn, db: Session = Depends(get_db)):
    v = svc.add_version(db, body.model_dump())
    return {"id": v.id}


@router.post("/clauses", response_model=ClauseOut)
def create_clause(body: ClauseIn, db: Session = Depends(get_db)):
    c = svc.add_clause(db, body.model_dump())
    return ClauseOut.model_validate(c)


@router.post("/variables", response_model=VariableOut)
def create_variable(body: VariableIn, db: Session = Depends(get_db)):
    v = svc.add_variable(db, body.model_dump())
    return VariableOut.model_validate(v)


@router.post("/render", response_model=RenderOut)
def post_render(body: RenderReq, db: Session = Depends(get_db)):
    try:
        out = svc.render(db, body.template_id, body.version, body.variables)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"rendered": out}


@router.post("/generate", response_model=DocOut)
def post_generate(body: GenerateReq, db: Session = Depends(get_db)):
    try:
        d = svc.generate_document(db, body.template_id, body.version, body.variables)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": d.id, "status": d.status}


@router.post("/sign", response_model=DocOut)
def post_sign(body: SignReq, db: Session = Depends(get_db)):
    enforce_engine("wholesaling", CONTRACT_SEND)
    try:
        d = svc.request_signature(db, body.document_id, body.signer_name, body.signer_email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": d.id, "status": d.status}
