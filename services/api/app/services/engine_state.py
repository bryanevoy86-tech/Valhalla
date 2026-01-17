from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.engines.states import EngineState, assert_transition, allowed_next_states
from app.models.engine_state import EngineStateRow


DEFAULT_ENGINES = [
    # Primary launch engine
    "wholesaling",
    # Future/dormant engines can be listed now safely
    "trading_advisory",
]


def _get_or_create(db: Session, engine_name: str) -> EngineStateRow:
    row = db.query(EngineStateRow).filter(EngineStateRow.engine_name == engine_name).first()
    if row:
        return row
    row = EngineStateRow(engine_name=engine_name, state=EngineState.DORMANT.value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_states(db: Session) -> list[Dict[str, Any]]:
    out: list[Dict[str, Any]] = []
    for name in DEFAULT_ENGINES:
        row = _get_or_create(db, name)
        cur = EngineState(row.state)
        out.append(
            {
                "engine_name": row.engine_name,
                "state": row.state,
                "allowed_next": [s.value for s in allowed_next_states(cur)],
                "changed_by": row.changed_by,
                "reason": row.reason,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        )
    return out


def get_state(db: Session, engine_name: str) -> EngineState:
    row = _get_or_create(db, engine_name)
    return EngineState(row.state)


def transition(
    db: Session,
    engine_name: str,
    target: EngineState,
    changed_by: str = "system",
    reason: str | None = None,
) -> Dict[str, Any]:
    row = _get_or_create(db, engine_name)
    cur = EngineState(row.state)
    assert_transition(cur, target)

    row.state = target.value
    row.changed_by = changed_by
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "engine_name": row.engine_name,
        "state": row.state,
        "allowed_next": [s.value for s in allowed_next_states(target)],
        "changed_by": row.changed_by,
        "reason": row.reason,
        "updated_at": row.updated_at.isoformat(),
    }
