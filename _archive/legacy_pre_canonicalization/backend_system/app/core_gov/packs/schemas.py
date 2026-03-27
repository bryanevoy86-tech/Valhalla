from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PackCreate(BaseModel):
    code: str                    # "P-OBLIG-1"
    name: str                    # "Household Obligations Registry"
    module: str                  # "backend.app.core_gov.obligations"
    router_symbol: str = ""      # "obligations_router" OR empty if none
    data_paths: List[str] = Field(default_factory=list)  # e.g. ["backend/data/obligations/obligations.json"]
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PackRecord(BaseModel):
    id: str
    code: str
    name: str
    module: str
    router_symbol: str = ""
    data_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PackListResponse(BaseModel):
    items: List[PackRecord]


class ValidateResponse(BaseModel):
    ok: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked: int = 0
