
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.db import Base, engine


# ensure models import somewhere before create_all
from .models import deal, lead, user  # noqa: F401

app = FastAPI(
    title=get_settings().PROJECT_NAME,
    openapi_url=f"{get_settings().API_V1_STR}/openapi.json",
)

# CORS for WeWeb, ngrok, local dev
origins = [
    "https://*.weweb.app",
    "https://*.ngrok-free.app",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-schema creation - disabled for local dev (use alembic migrations instead)
# Base.metadata.create_all(bind=engine)

# Viability Core routers (Policy, Health, Telemetry, Exports)
try:
    from .core.policy.router import router as policy_router
    from .core.health.router import router as health_router
    from .core.telemetry.router import router as telemetry_router
    from .core.exports.router import router as exports_router

    app.include_router(health_router)
    app.include_router(policy_router)
    app.include_router(telemetry_router)
    app.include_router(exports_router)
except Exception as e:
    print(f"WARNING: Could not load Viability Core routers: {e}")

# route mounting (only add if not present)
try:
    s = get_settings()
    from ..routes.progress import router as progress_router
    from ..routes.uploads import router as uploads_router
    from .api.routes import auth, buyers, deals, files, health, jobs, leads, underwriting, users
    from .routers import audit as audit_router
    from .routers import billing as billing_router

    app.include_router(health.router)
    app.include_router(auth.router, prefix=s.API_V1_STR)
    app.include_router(users.router, prefix=s.API_V1_STR)
    app.include_router(leads.router, prefix=s.API_V1_STR)
    app.include_router(deals.router, prefix=s.API_V1_STR)
    app.include_router(underwriting.router, prefix=s.API_V1_STR)
    app.include_router(buyers.router, prefix=s.API_V1_STR)
    app.include_router(jobs.router, prefix=s.API_V1_STR)
    app.include_router(files.router, prefix=s.API_V1_STR)
    app.include_router(audit_router.router, prefix=f"{s.API_V1_STR}")
    app.include_router(billing_router.router, prefix=f"{s.API_V1_STR}")
    app.include_router(uploads_router, prefix="/api")
    app.include_router(progress_router, prefix="/api")
except Exception:
    pass

# Request ID middleware for audit/request correlation
from .deps.request_ctx import get_request_id


@app.middleware("http")
async def _ensure_request_id(request, call_next):
    get_request_id(request)
    return await call_next(request)


# Event bus, admin bootstrap, and autogen router loader
try:
    from ..autogen_loader import load_autogen_routers
    from .core.startup import attach_event_handlers, ensure_admin

    @app.on_event("startup")
    def _on_startup():
        ensure_admin()
        attach_event_handlers()
        load_autogen_routers(app)

except Exception:
    pass


from app.observability.logging import configure_logging
from app.observability.metrics import install_metrics
from app.observability.replay import install_replay_middleware
from app.observability.tracing import setup_tracing
from app.routers import (
    admin_alerts,
    admin_canary,
    # admin_logs,  # TODO: implement
    admin_observability,
    # admin_ops,  # TODO: implement
    admin_replay,
)
from fastapi.staticfiles import StaticFiles

configure_logging()
setup_tracing(app)
install_metrics(app)
install_replay_middleware(app)
app.include_router(admin_observability.router)
# app.include_router(admin_logs.router)  # TODO: implement
app.include_router(admin_replay.router)
# app.include_router(admin_ops.router)  # TODO: implement
app.include_router(admin_alerts.router)
app.include_router(admin_canary.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


from app.observability import canary
from app.observability.logging import get_logger
from app.observability.metrics import NS, Counter, _registry
from fastapi import Request

log_canary = get_logger("canary")
CANARY_ROUTED = Counter(
    f"{NS}_canary_routed_total", "Requests routed to canary", ["path"], registry=_registry
)
CANARY_FALLBACK = Counter(
    f"{NS}_canary_fallback_total",
    "Requests failed canary and fell back",
    ["path"],
    registry=_registry,
)


@app.middleware("http")
async def canary_splitter(request: Request, call_next):
    st = canary.status()
    if not st.get("enabled") or st.get("percent", 0) <= 0:
        return await call_next(request)

    path = request.url.path
    headers = dict(request.headers)
    cookies = request.cookies or {}
    should_canary = canary.decide(path, headers, cookies)

    if not should_canary:
        return await call_next(request)

    target = f'{st["upstream"]}{path}'
    if request.url.query:
        target += f"?{request.url.query}"
    body = await request.body()

    try:
        resp = await canary.proxy_request(request.method, target, body, headers)
        CANARY_ROUTED.labels(path=path).inc()
        if canary.STICKY_COOKIE:
            resp_headers = dict(resp.headers)
            from starlette.responses import Response as SR

            out = SR(content=resp.content, status_code=resp.status_code, headers=resp_headers)
            out.set_cookie(canary.STICKY_COOKIE, "1", max_age=3600, path="/")
            return out
        else:
            from fastapi.responses import Response as FR

            return FR(content=resp.content, status_code=resp.status_code, headers=resp.headers)
    except Exception as e:
        canary.record_failure()
        CANARY_FALLBACK.labels(path=path).inc()
        log_canary.error("canary.proxy.error", path=path, err=str(e))
        return await call_next(request)


from app.routers import admin_bluegreen, admin_health

app.include_router(admin_health.router)
app.include_router(admin_bluegreen.router)

from app.observability.ratelimit import middleware as rl_mw


@app.middleware("http")
async def rl_wrapper(request, call_next):
    return await rl_mw(request, call_next)


import asyncio
import os

import httpx

BG_ON = os.getenv("BG_ENABLED", "false").lower() in ("1", "true", "yes")
BG_BLUE = os.getenv("BG_BLUE_UPSTREAM", "http://backend:8000").rstrip("/")
BG_GREEN = os.getenv("BG_GREEN_UPSTREAM", "http://backend-green:8000").rstrip("/")
BG_ACTIVE = os.getenv("BG_ACTIVE", "blue")


@app.middleware("http")
async def bluegreen_proxy(request, call_next):
    if not BG_ON:
        return await call_next(request)
    base = BG_BLUE if BG_ACTIVE == "blue" else BG_GREEN
    url = f"{base}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            rr = await cli.request(request.method, url, content=body, headers=dict(request.headers))
        from fastapi.responses import Response as FR

        return FR(content=rr.content, status_code=rr.status_code, headers=rr.headers)
    except Exception:
        return await call_next(request)


from app.routers import admin_sla

app.include_router(admin_sla.router)
from app.observability import tenant


@app.middleware("http")
async def tenant_mw(request, call_next):
    return await tenant.middleware(request, call_next)


@app.on_event("startup")
async def _warm():
    from app.observability import synthetic, warmer

    asyncio.create_task(warmer.run())
    asyncio.create_task(synthetic.run())
