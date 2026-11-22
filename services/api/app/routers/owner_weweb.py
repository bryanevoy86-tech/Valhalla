"""Write-side owner browser routes over the existing private JARVIS store."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.routers.auth_weweb import private_owner_response, require_owner_session
from app.services.owner_startup import StartupPlanIn, prepare_startup
from app.services.owner_conversation import (
    ThreadIn, TurnIn, UploadIn, attachment_summaries, bounded_upload, create_conversation, local_extraction,
    store_attachment, submit_turn,
)

router = APIRouter(prefix="/api/weweb", tags=["weweb-owner-conversation"],
                   dependencies=[Depends(require_owner_session)])


@router.post("/owner-conversations", status_code=201)
def owner_create_conversation(payload: ThreadIn, db: Session = Depends(get_db)):
    return private_owner_response(create_conversation(payload, db), status_code=201)


@router.post("/owner-conversations/{conversation_id}/turns", status_code=201)
def owner_submit_turn(conversation_id: UUID, payload: TurnIn, db: Session = Depends(get_db)):
    return private_owner_response(submit_turn(conversation_id, payload, db, local_only=True), status_code=201)


@router.post("/owner-conversations/{conversation_id}/attachments", status_code=201)
def owner_upload_attachment(conversation_id: UUID, payload: UploadIn = Depends(bounded_upload),
                            db: Session = Depends(get_db)):
    return private_owner_response(store_attachment(conversation_id, payload, db), status_code=201)


@router.post("/owner-conversations/{conversation_id}/attachments/{attachment_id}/extract")
def owner_extract_attachment(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(local_extraction(conversation_id, attachment_id, db))


@router.get("/owner-conversations/{conversation_id}/attachments")
def owner_list_attachments(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
    return private_owner_response(attachment_summaries(conversation_id, limit, db))


@router.post("/owner-startup/compare")
def startup_comparison(payload: StartupPlanIn):
    return private_owner_response(prepare_startup(payload))


class AttentionAcknowledgmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notification_id: str = Field(min_length=3, max_length=128)


@router.get("/owner-attention")
def attention_inbox(db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import owner_attention_with_acknowledgments

    return private_owner_response(owner_attention_with_acknowledgments(db, owner_id))


@router.post("/owner-attention/acknowledge")
def attention_acknowledge(payload: AttentionAcknowledgmentIn, db: Session = Depends(get_db),
                          owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import acknowledge_owner_attention

    return private_owner_response(acknowledge_owner_attention(db, owner_id, payload.notification_id))
