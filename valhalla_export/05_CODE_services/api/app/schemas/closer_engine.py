# services/api/app/schemas/closer_engine.py

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CloserSessionStartRequest(BaseModel):
    """
    Start a closing session for a given backend deal.
    """

    backend_deal_id: int = Field(
        ...,
        description="Backend Deal.id to run the closing session for.",
    )
    channel: Literal["phone", "zoom", "in_person"] = Field(
        default="phone",
        description="Channel of the conversation (for script tone).",
    )
    role: Literal["acquisition", "disposition"] = Field(
        default="acquisition",
        description="Which side you're closing from.",
    )


class CloserSessionContext(BaseModel):
    """
    Snapshot of what the closer needs at the start of the call.
    """

    closing_context: Dict[str, Any]
    closing_playbook: Dict[str, Any]


class CloserSessionStartResponse(BaseModel):
    """
    Response from starting a closing session.
    """

    session_id: str
    backend_deal_id: int
    channel: str
    role: str
    context: CloserSessionContext
    opening_line: str
    first_prompts: List[str]


class CloserNextBlockRequest(BaseModel):
    """
    Request the next set of prompts in the script.

    This is deliberately simple for now; Heimdall or your UI can maintain
    the true transcript state.
    """

    session_id: str
    backend_deal_id: int
    last_section: Literal[
        "opening",
        "rapport",
        "diagnostic",
        "numbers",
        "offer",
        "objections",
        "closing",
    ] = Field(
        ...,
        description="Which part of the script you just finished.",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Optional short summary of how that section went.",
    )


class CloserNextBlockResponse(BaseModel):
    """
    Suggested next section of the playbook.
    """

    session_id: str
    backend_deal_id: int
    next_section: Literal[
        "opening",
        "rapport",
        "diagnostic",
        "numbers",
        "offer",
        "objections",
        "closing",
        "done",
    ]
    prompts: List[str] = Field(
        default_factory=list,
        description="Lines/questions to use in this section.",
    )
    notes: Optional[str] = None


class CloserFeedbackRequest(BaseModel):
    """
    After a call, log what happened in a lightweight way.
    """

    session_id: str
    backend_deal_id: int
    disposition: Literal["won", "lost", "maybe", "no_show"] = Field(
        ...,
        description="High-level outcome of the call.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Why you think the call went that way.",
    )
    next_steps: Optional[str] = Field(
        default=None,
        description="What you plan to do next for this deal.",
    )


class CloserFeedbackResponse(BaseModel):
    """
    Simple acknowledgement for now.
    """

    session_id: str
    backend_deal_id: int
    disposition: str
    stored: bool
    notes: Optional[str] = None


class CloserTranscriptStub(BaseModel):
    """
    Placeholder while full transcript storage is not implemented.
    """

    session_id: str
    backend_deal_id: int
    status: str
    message: str
