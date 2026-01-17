from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from ..audit.audit_log import audit
from ..cone.service import get_cone_state
from ..health.status import ryg_status
from .session_store import load_session, save_session
from .session_models import GoSession

def get_session() -> GoSession:
    s = load_session()
    if not s:
        return GoSession(active=False)
    return GoSession(**s)

def start_session(notes: str | None = None) -> GoSession:
    cone = get_cone_state()
    status = ryg_status()

    now = dt.datetime.utcnow().isoformat() + "Z"

    snapshot = {
        "cone": cone.model_dump(),
        "status": {
            "status": status.get("status"),
            "reasons": status.get("reasons", [])[:10],
        },
    }

    sess = GoSession(
        active=True,
        started_at_utc=now,
        ended_at_utc=None,
        cone_band=cone.band,
        status=status.get("status"),
        notes=notes,
        snapshot=snapshot,
    )

    save_session(sess.model_dump())
    audit("GO_SESSION_START", {"started_at_utc": now, "cone_band": cone.band, "status": sess.status, "notes": notes or ""})
    return sess

def end_session(notes: str | None = None) -> GoSession:
    existing = get_session()
    now = dt.datetime.utcnow().isoformat() + "Z"

    sess = GoSession(
        active=False,
        started_at_utc=existing.started_at_utc,
        ended_at_utc=now,
        cone_band=existing.cone_band,
        status=existing.status,
        notes=notes or existing.notes,
        snapshot=existing.snapshot,
    )
    save_session(sess.model_dump())
    audit("GO_SESSION_END", {"ended_at_utc": now, "notes": notes or ""})
    return sess
