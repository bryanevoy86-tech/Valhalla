from fastapi import APIRouter

from app.core.runbook.blockers import evaluate_core_blockers

router = APIRouter(prefix="/api/runbook", tags=["runbook"])


@router.get("/status")
def runbook_status():
    """
    Always returns status.
    Never raises 500.
    """
    try:
        return evaluate_core_blockers()
    except Exception as e:
        return {
            "ok": False,
            "blockers": [f"runbook evaluation error: {e}"],
            "warnings": [],
        }
