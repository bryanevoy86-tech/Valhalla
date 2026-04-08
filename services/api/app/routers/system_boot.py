import asyncio
from fastapi import APIRouter

from app.services.post_boot_init import get_init_state, run_post_boot_init, run_post_boot_init_sync

router = APIRouter(prefix="/admin/system/init", tags=["system-init"])


@router.get("/status")
def init_status():
    return {"ok": True, "init": get_init_state()}


@router.post("/run")
async def init_run():
    asyncio.create_task(run_post_boot_init(delay_seconds=1))
    return {"ok": True, "queued": True, "message": "Post-boot init queued."}


@router.post("/run-now")
def init_run_now():
    result = run_post_boot_init_sync()
    return {"ok": result.get("ok", False), "result": result}
