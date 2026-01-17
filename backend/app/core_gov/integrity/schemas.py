from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    ok: bool
    checks_run: int
    passed: int
    failed: int
    results: List[Dict[str, Any]] = Field(default_factory=list)
