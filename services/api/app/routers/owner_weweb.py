"""Write-side owner browser routes over the existing private JARVIS store."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.routers.auth_weweb import private_owner_response, require_owner_session
from app.services.owner_document_requests import (
    DocumentApplyIn, DocumentRequestIn, apply_document_request, document_request_status, request_document_action,
)
from app.services.owner_specialist_context import prime_decision_context, specialist_context
from app.services.prime_business_execution import require_owner_mandate_key
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


class AttentionEntry(BaseModel):
    notification_id: str
    category: Literal["integrity", "prime_integrity", "review", "prime_advisory", "economic", "discovery", "schedule"]
    reference: str


class AttentionInboxOut(BaseModel):
    entries: list[AttentionEntry]
    acknowledged_ids: list[str]
    view: Literal["PRIVATE_IN_APP"]
    delivery_attempted: Literal[False]
    execution_authorized: Literal[False]


class AttentionAcknowledgmentOut(BaseModel):
    notification_id: str
    acknowledged: Literal[True]
    delivery_attempted: Literal[False]
    execution_authorized: Literal[False]


@router.get("/owner-attention", response_model=AttentionInboxOut)
def attention_inbox(db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import owner_attention_with_acknowledgments

    inbox = AttentionInboxOut.model_validate(owner_attention_with_acknowledgments(db, owner_id))
    return private_owner_response(inbox)


@router.post("/owner-attention/acknowledge", response_model=AttentionAcknowledgmentOut)
def attention_acknowledge(payload: AttentionAcknowledgmentIn, db: Session = Depends(get_db),
                          owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import acknowledge_owner_attention

    receipt = AttentionAcknowledgmentOut.model_validate(acknowledge_owner_attention(db, owner_id, payload.notification_id))
    return private_owner_response(receipt)


@router.post("/owner-conversations/{conversation_id}/attachments/{attachment_id}/requests", status_code=201)
def stage_document_request(conversation_id: UUID, attachment_id: UUID, payload: DocumentRequestIn,
                           db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(request_document_action(db, owner_id, conversation_id, attachment_id, payload),
                                  status_code=201)


@router.get("/owner-document-requests/{request_id}")
def owner_document_request(request_id: UUID, db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(document_request_status(db, owner_id, request_id))


@router.post("/owner-document-requests/{request_id}/apply", dependencies=[Depends(require_owner_mandate_key)])
def owner_apply_document_request(request_id: UUID, payload: DocumentApplyIn,
                                 db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(apply_document_request(db, owner_id, request_id, payload.expected_sha256))


@router.get("/owner-prime-decisions/{decision_id}")
def owner_prime_decision(decision_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(prime_decision_context(db, decision_id))


@router.get("/owner-specialist-schedules/{schedule_id}")
def owner_specialist_receipt(schedule_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(specialist_context(db, schedule_id, require_digest=True))
