"""
Pack 51: Legal Document Engine - Service layer
"""
import json, re
from sqlalchemy.orm import Session
from app.legal.models import (
    LegalTemplate, LegalTemplateVersion, LegalClause, LegalVariable, LegalDocument
)

_VAR_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_:]+)\s*}}")


def upsert_template(db: Session, body: dict):
    t = LegalTemplate(**body)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def add_version(db: Session, body: dict):
    v = LegalTemplateVersion(**body)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def add_clause(db: Session, body: dict):
    c = LegalClause(**body)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def add_variable(db: Session, body: dict):
    v = LegalVariable(**body)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _validate_vars(db: Session, vars: dict):
    req = db.query(LegalVariable).filter(LegalVariable.required == True).all()
    missing = [r.key for r in req if r.key not in vars]
    return missing


def render(db: Session, template_id: int, version: int, variables: dict) -> str:
    tv = (
        db.query(LegalTemplateVersion)
        .filter(
            LegalTemplateVersion.template_id == template_id,
            LegalTemplateVersion.version == version,
        )
        .first()
    )
    if not tv:
        raise ValueError("Template version not found")

    missing = _validate_vars(db, variables)
    if missing:
        raise ValueError(f"Missing required variables: {', '.join(missing)}")

    def repl(m):
        key = m.group(1)
        if key.startswith("clause:"):
            name = key.split(":", 1)[1]
            c = db.query(LegalClause).filter(LegalClause.name == name).first()
            return c.body if c else f"[MISSING CLAUSE: {name}]"
        return str(variables.get(key, f"[MISSING:{key}]"))

    return _VAR_PATTERN.sub(repl, tv.body)


def generate_document(db: Session, template_id: int, version: int, variables: dict):
    body = render(db, template_id, version, variables)
    d = LegalDocument(
        template_id=template_id,
        version=version,
        rendered_body=body,
        variables_json=json.dumps(variables),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def request_signature(db: Session, doc_id: int, signer_name: str, signer_email: str):
    from app.core.engines.dispatch_guard import guard_contract_send
    guard_contract_send()
    d = db.query(LegalDocument).get(doc_id)
    if not d:
        raise ValueError("Document not found")
    # Stub DocuSign request
    ext = f"ENV-{d.id:06d}"
    d.external_ref = ext
    d.status = "sent"
    db.commit()
    db.refresh(d)
    return d
