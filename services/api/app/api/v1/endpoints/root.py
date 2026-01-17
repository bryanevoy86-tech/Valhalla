from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="API V1 Root")
async def root():
    return {"status": "ok", "version": "v1"}
