from __future__ import annotations

from .session_service import get_session
from .service import next_step, build_checklist
from ..health.status import ryg_status
from ..cone.service import get_cone_state

def go_summary() -> dict:
    """Unified GO summary - all data needed for WeWeb Go Mode page."""
    return {
        "session": get_session().model_dump(),
        "next": next_step().model_dump(),
        "checklist": build_checklist().model_dump(),
        "health": {
            "status": ryg_status(),
            "cone": get_cone_state().model_dump(),
        },
    }
