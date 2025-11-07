"""Pack 63: Closer Engine Router (stub)"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/closer", tags=["closer"])

class SessionStart(BaseModel):
    deal_id: int
    contact_id: str
    tone_hint: Optional[str] = None

class SellerFeedback(BaseModel):
    session_id: int
    sentiment: float
    objection: Optional[str] = None
    message: Optional[str] = None

@router.post("/session/start")
def start_session(payload: SessionStart):
    return {"session_id": 9001, "block": {"namespace":"intro","content":"Hi, thanks for taking my call..."}}

@router.post("/session/next")
def next_block(session_id: int, outcome: str = "continue"):
    return {"session_id": session_id, "block": {"namespace":"qualify","content":"Quick question about the property..."}}

@router.post("/session/feedback")
def feedback(data: SellerFeedback):
    return {"ok": True}

@router.get("/session/{session_id}/transcript")
def transcript(session_id: int):
    return {"session_id": session_id, "events": []}
