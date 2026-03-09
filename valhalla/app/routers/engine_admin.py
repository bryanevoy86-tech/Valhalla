from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.engines.heimdall_runtime import heimdall_engine_authority
from app.core.engines.errors import EngineTransitionDenied
from app.core.engines.states import EngineState
from app.core.engines.transition_service import request_transition

router = APIRouter(prefix="/api/engines", tags=["engines"])


class TransitionBody(BaseModel):
    engine_name: str
    target_state: EngineState

    # Wire these to real metrics later (or keep 0 until you add the metrics endpoint)
    monthly_net_cad: float = 0.0
    monthly_burn_cad: float = 200.0
    critical_runbook_blockers: int = 0


@router.get("/states")
def get_states():
    return {"states": heimdall_engine_authority.get_all_states()}


@router.post("/transition")
def transition(body: TransitionBody):
    try:
        return request_transition(
            engine_name=body.engine_name,
            target_state=body.target_state,
            monthly_net_cad=body.monthly_net_cad,
            monthly_burn_cad=body.monthly_burn_cad,
            critical_runbook_blockers=body.critical_runbook_blockers,
        )
    except EngineTransitionDenied as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"unexpected error: {e}")
