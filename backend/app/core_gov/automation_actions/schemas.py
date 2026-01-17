from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class GenerateFollowupsRequest(BaseModel):
    lookahead_days: int = 14
    dedupe_days: int = 21
    max_create: int = 30
    mode: Literal["explore", "execute"] = "execute"
    meta: Dict[str, Any] = Field(default_factory=dict)


class GenerateFollowupsResponse(BaseModel):
    created: int = 0
    attempted: int = 0
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
