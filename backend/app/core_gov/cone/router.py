from fastapi import APIRouter, Depends
from ..canon.canon import ConeBand
from .models import ConeDecision, ConeState
from .service import decide, get_cone_state, set_cone_state
from ..security.rbac import require_scopes, require_active_subscription
from ..security.devkey.deps import require_dev_key
from ..rate_limit.deps import rate_limit

router = APIRouter(prefix="/cone", tags=["Core: Cone"])

@router.get("/state", response_model=ConeState)
def read_state():
    return get_cone_state()

@router.post("/state", response_model=ConeState)
def write_state(
    band: ConeBand,
    reason: str,
    _key=Depends(require_dev_key),
    _sub=Depends(require_active_subscription),
    _owner=require_scopes("owner"),
    _rl=rate_limit("cone_set", max_requests=10, window_seconds=60),
):
    return set_cone_state(band=band, reason=reason)

@router.get("/decide", response_model=ConeDecision)
def read_decision(engine: str, action: str):
    return decide(engine_name=engine, action=action)
