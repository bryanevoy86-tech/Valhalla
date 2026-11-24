"""Go-Live service.

Prime Laws enforced:
- Human override is absolute (but logged).
- Sandbox before reality (enforcement only activates when configured).
- All actions logged, attributable, reversible.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.go_live_state import GoLiveState
from app.models.system_metadata import SystemMetadata
from app.services.system_status import get_packs


DEFAULT_ROW_ID = 1
RELEASE_EVIDENCE_BLOCKER = "OPERATIONAL_RELEASE_EVIDENCE_NOT_CONNECTED"


def _get_or_create(db: Session) -> GoLiveState:
    row = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).first()
    if row:
        return row
    row = GoLiveState(id=DEFAULT_ROW_ID, go_live_enabled=False, kill_switch_engaged=False)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        winner = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).first()
        if winner is None:
            raise
        return winner
    db.refresh(row)
    return row


def read_state(db: Session) -> GoLiveState:
    return _get_or_create(db)


def _check_backend_complete(db: Session) -> Tuple[bool, str]:
    meta = db.query(SystemMetadata).filter(SystemMetadata.id == 1).first()
    if not meta:
        return False, "system_metadata row missing"
    if not meta.backend_complete:
        return False, "backend_complete is False"
    return True, "backend_complete True"


def _check_required_packs_installed() -> Tuple[bool, Dict[str, Any]]:
    packs = get_packs()
    missing = [p["id"] for p in packs if p.get("status") != "installed"]
    return (len(missing) == 0), {"missing_or_not_installed": missing, "total": len(packs)}


def checklist(db: Session) -> Dict[str, Any]:
    ok_backend, backend_msg = _check_backend_complete(db)
    ok_packs, packs_info = _check_required_packs_installed()

    required = {
        "backend_complete": {"ok": ok_backend, "detail": backend_msg},
        "packs_installed": {"ok": ok_packs, "detail": packs_info},
    }

    # Historical flags are inventory only. No certified release evidence collector exists.
    required["operational_release_evidence"] = {
        "ok": False, "detail": RELEASE_EVIDENCE_BLOCKER,
    }
    state = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).first()
    required["emergency_stop_clear"] = {
        "ok": state is not None and state.kill_switch_engaged is False,
        "detail": "Persisted control state must exist and emergency stop must be clear",
    }
    warnings: Dict[str, Any] = {"historical_metadata_only": True}
    ok = all(item["ok"] for item in required.values())
    return {"ok": ok, "required": required, "warnings": warnings}


def set_go_live(db: Session, enabled: bool, changed_by: str, reason: str | None) -> GoLiveState:
    if type(enabled) is not bool:
        raise ValueError("enabled must be boolean")
    if enabled:
        raise HTTPException(status_code=412, detail=RELEASE_EVIDENCE_BLOCKER)
    _get_or_create(db)
    row = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).with_for_update().one()
    row.go_live_enabled = False
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def set_kill_switch(db: Session, engaged: bool, changed_by: str, reason: str | None) -> GoLiveState:
    if type(engaged) is not bool:
        raise ValueError("engaged must be boolean")
    _get_or_create(db)
    row = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).with_for_update().one()
    row.kill_switch_engaged = engaged
    # Releasing the stop is not permission to resume live effects.
    row.go_live_enabled = False
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
