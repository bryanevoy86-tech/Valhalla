import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import drift, retention

# --- Core FastAPI app ---------------------------------------------------------

app = FastAPI(
    title="Valhalla API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- System endpoints: root + health -----------------------------------------

@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint – Heimdall status + welcome message.
    """
    return {
        "message": "Welcome to Valhalla Legacy API",
        "status": "Heimdall Operational",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
async def health():
    """
    Simple health check for uptime monitors and Render.
    """
    return {"status": "ok", "heimdall": "online"}


@app.get("/healthz", tags=["System"])
async def healthz():
    """
    Secondary health endpoint (some scripts/tools use /healthz).
    """
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"service": "valhalla-api", "version": "1.0.0"}


@app.get("/api/features")
def features():
    return [{"id": 1, "name": "valhalla"}]


# --- API v1 router (optional, but safe) --------------------------------------

try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping /api/v1 router: {e}")

try:
    from app.routers.loki import router as loki_router
    app.include_router(loki_router)
except Exception as e:
    print(f"[app.main] Skipping loki router: {e}")

try:
    from app.routers.god_cases import router as god_cases_router
    app.include_router(god_cases_router)
except Exception as e:
    print(f"[app.main] Skipping god_cases router: {e}")

try:
    from app.routers.sync_engine import router as sync_engine_router
    app.include_router(sync_engine_router)
except Exception as e:
    print(f"[app.main] Skipping sync_engine router: {e}")

try:
    from app.routers.specialists import router as specialists_router
    app.include_router(specialists_router)
except Exception as e:
    print(f"[app.main] Skipping specialists router: {e}")

try:
    from app.routers.lawyer_feed import router as lawyer_feed_router
    app.include_router(lawyer_feed_router)
except Exception as e:
    print(f"[app.main] Skipping lawyer_feed router: {e}")

try:
    from app.routers.tax_bridge import router as tax_bridge_router
    app.include_router(tax_bridge_router)
except Exception as e:
    print(f"[app.main] Skipping tax_bridge router: {e}")

try:
    from app.routers.god_verdicts import router as god_verdicts_router
    app.include_router(god_verdicts_router)
except Exception as e:
    print(f"[app.main] Skipping god_verdicts router: {e}")

try:
    from app.routers.disputes import router as disputes_router
    app.include_router(disputes_router)
except Exception as e:
    print(f"[app.main] Skipping disputes router: {e}")

try:
    from app.routers.god_arbitration import router as god_arbitration_router
    app.include_router(god_arbitration_router)
except Exception as e:
    print(f"[app.main] Skipping god_arbitration router: {e}")

try:
    from app.routers.specialist_feedback import router as specialist_feedback_router
    app.include_router(specialist_feedback_router)
except Exception as e:
    print(f"[app.main] Skipping specialist_feedback router: {e}")

try:
    from app.api.v1.backup import router as backup_router
    app.include_router(backup_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping backup router: {e}")

try:
    from app.api.v1.security import router as security_router
    app.include_router(security_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping security router: {e}")

try:
    from app.api.v1.optimization import router as optimization_router
    app.include_router(optimization_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping optimization router: {e}")

try:
    from app.api.v1.telemetry import router as telemetry_router
    app.include_router(telemetry_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping telemetry router: {e}")

try:
    from app.api.v1.diagnostics import router as diagnostics_router
    app.include_router(diagnostics_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping diagnostics router: {e}")

try:
    from app.api.v1.bus import router as bus_router
    app.include_router(bus_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping bus router: {e}")


# --- Startup tasks ------------------------------------------------------------

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
