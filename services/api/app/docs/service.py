import re
from sqlalchemy.orm import Session
from app.docs.models import DocTemplate, GeneratedDoc
from app.docs import schemas
from app.finops import service as finops_service
from app.finops.schemas import ESignCreate


PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def create_template(db: Session, data: schemas.DocTemplateCreate) -> DocTemplate:
    tpl = DocTemplate(**data.model_dump())
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def list_templates(db: Session) -> list[DocTemplate]:
    return db.query(DocTemplate).order_by(DocTemplate.id.desc()).all()


def generate_document(db: Session, request: schemas.GenerateDocRequest) -> GeneratedDoc:
    tpl = db.query(DocTemplate).filter(DocTemplate.id == request.template_id).first()
    if not tpl:
        raise ValueError("Template not found")

    def replace_fn(match):
        key = match.group(1)
        return str(request.fields.get(key, f"{{{{{key}}}}}"))

    rendered = PLACEHOLDER_PATTERN.sub(replace_fn, tpl.content)
    doc = GeneratedDoc(
        template_id=tpl.id,
        filename=request.filename,
        content=rendered,
        meta=request.meta or {},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_generated(db: Session) -> list[GeneratedDoc]:
    return db.query(GeneratedDoc).order_by(GeneratedDoc.id.desc()).all()


def send_for_esign(db: Session, request: schemas.SendForESignRequest) -> dict:
    doc = db.query(GeneratedDoc).filter(GeneratedDoc.id == request.generated_doc_id).first()
    if not doc:
        raise ValueError("GeneratedDoc not found")

    esign_req = ESignCreate(
        recipients=request.recipients,
        meta={"generated_doc_id": doc.id, "filename": doc.filename},
    )
    env = finops_service.create_envelope(db, esign_req)
    return {"envelope_id": env.id, "status": env.status}
