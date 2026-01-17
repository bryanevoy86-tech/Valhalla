"""PACK 91: Legal Drafting - Service"""

from sqlalchemy.orm import Session

from app.models.legal_drafting import LegalTemplate, LegalDraft
from app.schemas.legal_drafting import LegalTemplateCreate, LegalDraftCreate


# Legal template operations
def create_template(db: Session, template: LegalTemplateCreate) -> LegalTemplate:
    db_template = LegalTemplate(
        title=template.title,
        category=template.category,
        body=template.body
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def list_templates(db: Session, category: str | None = None) -> list[LegalTemplate]:
    q = db.query(LegalTemplate)
    if category:
        q = q.filter(LegalTemplate.category == category)
    return q.order_by(LegalTemplate.id.desc()).all()


def get_template(db: Session, template_id: int) -> LegalTemplate | None:
    return db.query(LegalTemplate).filter(LegalTemplate.id == template_id).first()


def update_template(db: Session, template_id: int, template: LegalTemplateCreate) -> LegalTemplate | None:
    db_template = get_template(db, template_id)
    if not db_template:
        return None
    db_template.title = template.title
    db_template.category = template.category
    db_template.body = template.body
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int) -> bool:
    db_template = get_template(db, template_id)
    if not db_template:
        return False
    db.delete(db_template)
    db.commit()
    return True


# Legal draft operations
def create_draft(db: Session, draft: LegalDraftCreate) -> LegalDraft:
    db_draft = LegalDraft(
        template_id=draft.template_id,
        filled_payload=draft.filled_payload,
        output_path=draft.output_path
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft


def list_drafts(db: Session, template_id: int | None = None) -> list[LegalDraft]:
    q = db.query(LegalDraft)
    if template_id:
        q = q.filter(LegalDraft.template_id == template_id)
    return q.order_by(LegalDraft.id.desc()).all()


def get_draft(db: Session, draft_id: int) -> LegalDraft | None:
    return db.query(LegalDraft).filter(LegalDraft.id == draft_id).first()


def update_draft(db: Session, draft_id: int, draft: LegalDraftCreate) -> LegalDraft | None:
    db_draft = get_draft(db, draft_id)
    if not db_draft:
        return None
    db_draft.template_id = draft.template_id
    db_draft.filled_payload = draft.filled_payload
    db_draft.output_path = draft.output_path
    db.commit()
    db.refresh(db_draft)
    return db_draft


def delete_draft(db: Session, draft_id: int) -> bool:
    db_draft = get_draft(db, draft_id)
    if not db_draft:
        return False
    db.delete(db_draft)
    db.commit()
    return True
