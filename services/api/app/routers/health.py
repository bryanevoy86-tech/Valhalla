from fastapi import APIRouter

router = APIRouter(prefix="/healthz", tags=["health"])


@router.get("")
async def healthz():
    return {"ok": True, "status": "ok", "app": "Valhalla API", "version": "3.4"}
