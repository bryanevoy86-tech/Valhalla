import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
import os
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from app.routers.admin_build import router as admin_build_router
from app.routers.admin_handoff import router as admin_handoff_router
from app.routers.admin_privacy import router as admin_privacy_router
from app.routers.admin_secscan import router as admin_secscan_router
 # Removed broken imports: leads_status, features, match, agreements, title
from app.observability import chaos, drift, geoip, retention, tenant_slo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permissive CORS for debugging; tighten later
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
    return {"message": "Welcome to Valhalla Legacy. Heimdall is online."}

# Retention cron
import asyncio


@app.on_event("startup")
async def _retention_cron():
    if not retention.EN:
        return

    async def loop():
        while True:
            await retention.run_once()
            await asyncio.sleep(int(os.getenv("RETENTION_CRON_MINUTES", "30")) * 60)

    asyncio.create_task(loop())


# Drift check
@app.on_event("startup")
async def _drift_check():
    drift.check()
