from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.core.engines.actions import EngineAction
from app.core.engines.errors import EngineBlocked
from app.core.engines.states import EngineState
from app.models.audit_log import AuditLog
from app.services.engine_state import get_state
from app.services.go_live import read_state


SHADOW_CANONICAL_STATE = "SHADOW"
SHADOW_BLOCK_EVENT = "shadow_action_blocked"


def enforce_engine(engine_name: str, action: EngineAction, details: dict | None = None) -> None:
    """
    Canon guard:
    - If kill switch engaged => block everything with 409
    - If action.real_world_effect and engine is SANDBOX/DORMANT/DISABLED => block with 409
    - ACTIVE allows real-world effects (still subject to downstream policy)
    """
    session_gen = get_db_session()
    try:
        db = next(session_gen)
    except StopIteration:
        _raise_block(None, engine_name, action, "UNKNOWN", "Could not get database session", details)
        return

    try:
        go = read_state(db)
        if getattr(go, "kill_switch_engaged", False):
            _raise_block(db, engine_name, action, SHADOW_CANONICAL_STATE, "Kill switch engaged", details)

        state = get_state(db, engine_name)

        if action.real_world_effect:
            if state in (EngineState.SANDBOX, EngineState.DORMANT, EngineState.DISABLED):
                _raise_block(
                    db,
                    engine_name,
                    action,
                    SHADOW_CANONICAL_STATE,
                    f"Engine state {state.value} blocks real-world effects",
                    details,
                )
    finally:
        try:
            db.close()
        except Exception:
            pass


def _raise_block(
    db: Session | None,
    engine_name: str,
    action: EngineAction,
    state: str,
    reason: str,
    details: dict | None = None,
) -> None:
    if db is not None:
        audit_db: Session | None = None
        try:
            audit_db = Session(bind=db.get_bind())
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "actor": "system",
                "legacy": "core",
                "blocked_action": action.name,
                "engine": engine_name,
                "state": state,
                "real_world_effect": action.real_world_effect,
                "reason": reason,
                "canonical_runtime_mode": SHADOW_CANONICAL_STATE,
                "policy_mode": SHADOW_CANONICAL_STATE,
                "provider": None,
                "correlation_id": None,
                "work_item_id": None,
            }
            if details:
                payload.update(details)
            audit_entry = AuditLog(
                deal_id=None,
                event_type=SHADOW_BLOCK_EVENT,
                event_source="system",
                message=reason,
                event_data=json.dumps(payload),
            )
            audit_db.add(audit_entry)

            # Backward compatibility for existing dashboards/tests still keyed to autonomy_action_blocked.
            legacy_entry = AuditLog(
                deal_id=None,
                event_type="autonomy_action_blocked",
                event_source="system",
                message=reason,
                event_data=json.dumps(payload),
            )
            audit_db.add(legacy_entry)
            audit_db.commit()
        except Exception:
            try:
                if audit_db is not None:
                    audit_db.rollback()
            except Exception:
                pass
            # Guard behavior must remain fail-closed even if audit persistence fails.
            pass
        finally:
            try:
                if audit_db is not None:
                    audit_db.close()
            except Exception:
                pass

    err = EngineBlocked(engine_name=engine_name, action=action.name, state=state, reason=reason)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "type": "https://valhalla/errors/engine-blocked",
            "title": "EngineBlocked",
            "engine": err.engine_name,
            "action": err.action,
            "state": err.state,
            "reason": err.reason,
            "canonical_runtime_mode": SHADOW_CANONICAL_STATE,
        },
    )
