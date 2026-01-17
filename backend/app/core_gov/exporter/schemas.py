from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BackupResult(BaseModel):
    ok: bool
    backup_id: str
    created_at: datetime
    file_path: str
    file_name: str
    bytes: int
    included_files: List[str] = Field(default_factory=list)


class BackupListResponse(BaseModel):
    items: List[BackupResult]
