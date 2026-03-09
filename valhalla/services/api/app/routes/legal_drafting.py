"""PACK 91: Legal Drafting - Routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.legal_drafting import LegalTemplateCreate, LegalTemplateOut, LegalDraftCreate, LegalDraftOut
from app.services import legal_drafting_service

router = APIRouter(
    prefix="/legal",
    tags=["legal_drafting"]
)


# Template endpoints
@router.post("/template", response_model=LegalTemplateOut)
def create_template(template: LegalTemplateCreate, db: Session = Depends(get_db)):
    return legal_drafting_service.create_template(db, template)


@router.get("/template/{template_id}", response_model=LegalTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    return legal_drafting_service.get_template(db, template_id)


@router.get("/templates", response_model=list[LegalTemplateOut])
def list_templates(category: str | None = None, db: Session = Depends(get_db)):
    return legal_drafting_service.list_templates(db, category)


@router.put("/template/{template_id}", response_model=LegalTemplateOut)
def update_template(template_id: int, template: LegalTemplateCreate, db: Session = Depends(get_db)):
    return legal_drafting_service.update_template(db, template_id, template)


@router.delete("/template/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    success = legal_drafting_service.delete_template(db, template_id)
    return {"deleted": success}


# Draft endpoints
@router.post("/draft", response_model=LegalDraftOut)
def create_draft(draft: LegalDraftCreate, db: Session = Depends(get_db)):
    return legal_drafting_service.create_draft(db, draft)


@router.get("/draft/{draft_id}", response_model=LegalDraftOut)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    return legal_drafting_service.get_draft(db, draft_id)


@router.get("/drafts", response_model=list[LegalDraftOut])
def list_drafts(template_id: int | None = None, db: Session = Depends(get_db)):
    return legal_drafting_service.list_drafts(db, template_id)


@router.put("/draft/{draft_id}", response_model=LegalDraftOut)
def update_draft(draft_id: int, draft: LegalDraftCreate, db: Session = Depends(get_db)):
    return legal_drafting_service.update_draft(db, draft_id, draft)


@router.delete("/draft/{draft_id}")
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    success = legal_drafting_service.delete_draft(db, draft_id)
    return {"deleted": success}
