import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import drift, retention
from app.api.v1.api import api_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/version")
def version():
    return {"service": "valhalla-api", "version": "0.1.0"}

@app.get("/api/features")
def features():
    return [{"id": 1, "name": "valhalla"}]

@app.get("/")
def root():
    return {
        "message": "Welcome to Valhalla Legacy API",
        "status": "Heimdall Operational",
        "version": "1.0.0"
    }

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def _retention_cron():
    if not retention.EN:
        return

    async def loop():
        while True:
            await retention.run_once()
            await asyncio.sleep(int(os.getenv("RETENTION_CRON_MINUTES", "30")) * 60)

    asyncio.create_task(loop())

@app.on_event("startup")
async def _drift_check():
    drift.check()
