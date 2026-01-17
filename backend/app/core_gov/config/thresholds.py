from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field

from ..storage.json_store import read_json, write_json

THRESHOLDS_PATH = Path("data") / "thresholds.json"

class Thresholds(BaseModel):
    # jobs
    max_failed_jobs_red: int = Field(default=1, ge=0)
    max_failed_jobs_yellow: int = Field(default=0, ge=0)

    # decision drift
    deny_rate_yellow: float = Field(default=0.25, ge=0, le=1)
    deny_rate_red: float = Field(default=0.35, ge=0, le=1)
    min_decisions_for_drift: int = Field(default=20, ge=0)

    # log signals
    unhandled_exceptions_red: int = Field(default=1, ge=0)

def load_thresholds() -> Thresholds:
    raw = read_json(THRESHOLDS_PATH)
    if not raw:
        t = Thresholds()
        save_thresholds(t)
        return t
    try:
        return Thresholds.model_validate(raw)
    except Exception:
        t = Thresholds()
        save_thresholds(t)
        return t

def save_thresholds(t: Thresholds) -> None:
    write_json(THRESHOLDS_PATH, t.model_dump())
