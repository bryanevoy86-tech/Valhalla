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

from app.models.go_live_state import GoLiveState
from app.models.system_metadata import SystemMetadata
from app.services.system_status import get_packs


DEFAULT_ROW_ID = 1


def _get_or_create(db: Session) -> GoLiveState:
    row = db.query(GoLiveState).filter(GoLiveState.id == DEFAULT_ROW_ID).first()
    if row:
        return row
    row = GoLiveState(id=DEFAULT_ROW_ID, go_live_enabled=False, kill_switch_engaged=False)
    db.add(row)
    db.commit()
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

    warnings: Dict[str, Any] = {}
    ok = all(item["ok"] for item in required.values())
    return {"ok": ok, "required": required, "warnings": warnings}


def set_go_live(db: Session, enabled: bool, changed_by: str, reason: str | None) -> GoLiveState:
    row = _get_or_create(db)
    row.go_live_enabled = bool(enabled)
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def set_kill_switch(db: Session, engaged: bool, changed_by: str, reason: str | None) -> GoLiveState:
    row = _get_or_create(db)
    row.kill_switch_engaged = bool(engaged)
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
