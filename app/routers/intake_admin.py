from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.data_intake.promote import promote_to_clean
from app.core.engines.errors import EngineBlocked

router = APIRouter(prefix="/api/intake/admin", tags=["intake-admin"])


class PromoteBody(BaseModel):
    item_id: str
    trust_tier: str = "T1"


@router.post("/promote")
def promote(body: PromoteBody):
    try:
        item = promote_to_clean(
            item_id=body.item_id,
            trust_tier=body.trust_tier,
        )
        return {"ok": True, "item": item.__dict__}
    except EngineBlocked as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
