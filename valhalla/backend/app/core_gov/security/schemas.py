from __future__ import annotations

from typing import Any, Dict, Literal
from pydantic import BaseModel, Field


Level = Literal["internal", "shareable", "strict"]


class RedactTextRequest(BaseModel):
    text: str
    level: Level = "shareable"


class RedactTextResponse(BaseModel):
    redacted: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class SanitizeManifestRequest(BaseModel):
    manifest: Dict[str, Any]
    level: Level = "shareable"


class SanitizeManifestResponse(BaseModel):
    manifest: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
