import asyncio
import importlib
import json
import logging
import os
import pkgutil
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers.system_boot import router as system_boot_router
from app.routers import jarvis
from app.services.post_boot_init import run_post_boot_init

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_ROOT / "heimdall" / "agent.config.json"


def _cfg_dict() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _queue_counts(cfg: dict) -> dict:
    qdir = Path(cfg.get("queue_dir", "heimdall/queue"))
    qdir.mkdir(parents=True, exist_ok=True)

    pending = 0
    working = 0
    done = 0
    errors = 0

    for p in qdir.glob("*"):
        name = p.name
        if name.endswith(".done.yaml"):
            done += 1
        elif name.endswith(".working.yaml"):
            working += 1
        elif name.endswith(".error.yaml"):
            errors += 1
        elif name.endswith(".yaml"):
            pending += 1

    return {
        "pending": pending,
        "working": working,
        "done": done,
        "errors": errors,
    }


def _heartbeat_info(cfg: dict) -> dict:
    hb_file = Path(
        (cfg.get("health", {}) or {}).get(
            "heartbeat_file",
            "heimdall/state/worker_heartbeat.json",
        )
    )

    if not hb_file.exists():
        return {"present": False, "age_seconds": None, "raw": None}

    try:
        payload = json.loads(hb_file.read_text(encoding="utf-8"))
        age = max(0.0, time.time() - float(payload.get("ts", 0)))
        return {"present": True, "age_seconds": age, "raw": payload}
    except Exception:
        return {"present": True, "age_seconds": None, "raw": None}


def _autoload_router_modules(app: FastAPI) -> int:
    """
    Automatically includes any router module under app/routers
    that exposes a variable named `router`.
    """
    loaded = 0
    routers_pkg = "app.routers"

    package = importlib.import_module(routers_pkg)
    package_path = Path(package.__file__).resolve().parent

    skip_modules = {"system_boot", "__init__"}

    for module_info in pkgutil.iter_modules([str(package_path)]):
        mod_name = module_info.name
        if mod_name in skip_modules:
            continue

        full_name = f"{routers_pkg}.{mod_name}"
        try:
            mod = importlib.import_module(full_name)
            router = getattr(mod, "router", None)
            if router is not None:
                app.include_router(router)
                loaded += 1
                log.info("Autoloaded router: %s", full_name)
        except Exception as e:
            log.exception("Failed loading router module %s: %s", full_name, e)

    return loaded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan - boots fast, then runs delayed init in background."""
    # Boot fast. Then trigger post-boot init (5 second delay to let health stabilize)
    asyncio.create_task(run_post_boot_init(delay_seconds=5))
    yield


# Create app once
app = FastAPI(
    title="Valhalla API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

# Register system boot router first (admin endpoints)
app.include_router(system_boot_router)

# Register Heimdall/Jarvis router
app.include_router(jarvis.router)

# Import all models upfront to register them with Base.metadata ONCE
# This prevents duplicate table registration when routers import models
from app import models  # noqa: F401

# Auto-load all other routers from app/routers
loaded_router_count = _autoload_router_modules(app)
log.info("Valhalla startup complete. Loaded %s router modules.", loaded_router_count)

# ============================================================================
# CORS Middleware - Enable browser requests from WeWeb
# ============================================================================
from app.core.settings import settings

# Add CORS middleware if origins are configured
if settings.cors_allowed_origins is not None and len(settings.cors_allowed_origins) > 0:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info("CORS enabled for origins: %s", settings.cors_allowed_origins)
else:
    log.warning("CORS not configured - set CORS_ALLOWED_ORIGINS env var for browser requests")

# ============================================================================
# Health/Status Endpoints
# ============================================================================

@app.get("/health")
def health():
    """Quick health check - always responds immediately."""
    return {
        "ok": True,
        "status": "ok",
        "heimdall": "online",
        "routers_loaded": loaded_router_count,
    }


@app.get("/healthz")
def healthz():
    """Kubernetes-style health check with queue info."""
    cfg = _cfg_dict()
    return {
        "ok": True,
        "time": datetime.now().isoformat(timespec="seconds"),
        "queue": _queue_counts(cfg),
        "routers_loaded": loaded_router_count,
    }


@app.get("/readyz")
def readyz():
    """Kubernetes-style readiness check with heartbeat and optional DB check."""
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)

    max_age = int((cfg.get("health", {}) or {}).get("ready_heartbeat_max_age_seconds", 45))
    hb_ok = hb["present"] and hb["age_seconds"] is not None and hb["age_seconds"] <= max_age

    db_ok = True
    require_db = bool((cfg.get("health", {}) or {}).get("ready_require_db", False))

    if require_db and os.getenv("DATABASE_URL"):
        try:
            from app.core.db import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
        except Exception:
            db_ok = False

    ok = db_ok and (hb_ok or not require_db)
    status = 200 if ok else 503

    return JSONResponse(
        {
            "ok": ok,
            "worker_heartbeat_ok": hb_ok,
            "worker_heartbeat_age_seconds": hb.get("age_seconds"),
            "db_ok": db_ok,
            "queue": _queue_counts(cfg),
            "routers_loaded": loaded_router_count,
        },
        status_code=status,
    )


@app.get("/metrics")
def metrics_json():
    """JSON metrics endpoint."""
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)

    metrics = {}
    try:
        mpath = Path(cfg.get("metrics_file", "heimdall/state/metrics.json"))
        if mpath.exists():
            metrics = json.loads(mpath.read_text(encoding="utf-8"))
    except Exception:
        metrics = {}

    return {
        "queue": _queue_counts(cfg),
        "heartbeat_age_seconds": hb.get("age_seconds"),
        "metrics": metrics,
        "routers_loaded": loaded_router_count,
    }


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
def metrics_prometheus():
    """Prometheus-format metrics endpoint."""
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)
    q = _queue_counts(cfg)

    lines = []

    def put(name: str, val, typ="gauge", help_txt=""):
        if help_txt:
            lines.append(f"# HELP {name} {help_txt}")
        if typ:
            lines.append(f"# TYPE {name} {typ}")
        lines.append(f"{name} {val}")

    put("heimdall_queue_pending", q["pending"], "gauge", "Pending queue items")
    put("heimdall_queue_working", q["working"], "gauge", "Working queue items")
    put("heimdall_queue_done", q["done"], "gauge", "Done queue items")
    put("heimdall_queue_errors", q["errors"], "gauge", "Errored queue items")
    put(
        "heimdall_worker_heartbeat_age_seconds",
        hb.get("age_seconds") or 1e9,
        "gauge",
        "Age of last worker heartbeat",
    )
    put("valhalla_router_modules_loaded", loaded_router_count, "gauge", "Loaded FastAPI router modules")

    return "\n".join(lines) + "\n"
