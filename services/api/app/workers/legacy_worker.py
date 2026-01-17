import asyncio

async def auto_clone_check_once():
    # Placeholder: would evaluate readiness, trigger clone workflows.
    return {"status": "ok", "clones_triggered": 0}

async def legacy_worker_loop(interval_seconds: int = 600):
    while True:
        await auto_clone_check_once()
        await asyncio.sleep(interval_seconds)
