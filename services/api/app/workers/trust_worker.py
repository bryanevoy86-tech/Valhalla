import asyncio

async def process_trusts_once():
    # Placeholder logic: would route income flows, update vault balances, etc.
    return {"status": "ok", "processed": 0}

async def trust_worker_loop(interval_seconds: int = 300):
    while True:
        await process_trusts_once()
        await asyncio.sleep(interval_seconds)
