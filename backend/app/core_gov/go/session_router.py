from fastapi import APIRouter
from pydantic import BaseModel

from .session_models import GoSession
from .session_service import get_session, start_session, end_session

router = APIRouter(prefix="/go", tags=["Core: Go"])

class SessionNotes(BaseModel):
    notes: str | None = None

@router.get("/session", response_model=GoSession)
def session():
    return get_session()

@router.post("/start_session", response_model=GoSession)
def start(payload: SessionNotes):
    return start_session(notes=payload.notes)

@router.post("/end_session", response_model=GoSession)
def end(payload: SessionNotes):
    return end_session(notes=payload.notes)
