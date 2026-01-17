from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.core.engines.actions import EngineAction
from app.core.engines.errors import EngineBlocked
from app.core.engines.states import EngineState
from app.services.engine_state import get_state
from app.services.go_live import read_state


def enforce_engine(engine_name: str, action: EngineAction) -> None:
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
        _raise_block(engine_name, action, "UNKNOWN", "Could not get database session")
        return

    try:
        go = read_state(db)
        if getattr(go, "kill_switch_engaged", False):
            _raise_block(engine_name, action, "ACTIVE", "Kill switch engaged")

        state = get_state(db, engine_name)

        if action.real_world_effect:
            if state in (EngineState.SANDBOX, EngineState.DORMANT, EngineState.DISABLED):
                _raise_block(engine_name, action, state.value, f"Engine state {state.value} blocks real-world effects")
    finally:
        try:
            db.close()
        except Exception:
            pass


def _raise_block(engine_name: str, action: EngineAction, state: str, reason: str) -> None:
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
        },
    )
