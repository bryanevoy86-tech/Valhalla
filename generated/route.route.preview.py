from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Route"])


@router.get("/ping")
async def route():
    return {"pong": true}
