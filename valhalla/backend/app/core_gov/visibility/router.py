"""Phone-first visibility endpoints - read-only system overview."""
from fastapi import APIRouter

from ..cone.service import get_cone_state
from ..canon.canon import ENGINE_CANON
from ..jobs.router import _JOBS

router = APIRouter(prefix="/visibility", tags=["Core: Visibility"])


@router.get("/summary")
def system_summary():
    """Single pane of glass: Cone state, engines, and jobs at a glance."""
    cone = get_cone_state()

    engines = [
        {
            "name": e.name,
            "class": e.engine_class,
            "year1_allowed": e.year1_allowed,
            "hard_cap_usd": e.hard_cap_usd,
        }
        for e in ENGINE_CANON.values()
    ]

    jobs = {
        "total": len(_JOBS),
        "failed": len([j for j in _JOBS.values() if j.status == "FAILED"]),
        "running": len([j for j in _JOBS.values() if j.status == "RUNNING"]),
    }

    return {
        "cone": cone,
        "engines": engines,
        "jobs": jobs,
    }
