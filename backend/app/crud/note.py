from sqlalchemy.orm import Session

from ..models.note import LeadNote
from ..schemas.note import LeadNoteCreate
from ..services import audit


def add_note(db: Session, lead_id: int, author_id: int, data: LeadNoteCreate) -> LeadNote:
    n = LeadNote(lead_id=lead_id, author_id=author_id, body=data.body.strip())
    db.add(n)
    db.commit()
    db.refresh(n)
    audit.log(
        db,
        actor_id=author_id,
        action="lead_note_create",
        entity="note",
        entity_id=n.id,
        extra={"lead_id": lead_id},
    )
    return n
