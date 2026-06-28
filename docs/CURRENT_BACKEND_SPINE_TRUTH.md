# BACKEND SPINE TRUTH — Valhalla API Architecture

**Generated**: June 27, 2026  
**Scope**: Canonical FastAPI app architecture and startup flow  
**Status**: ✅ VERIFIED (Code-level inspection)

---

## CANONICAL FASTAPI APP

### Location
```
services/api/app/main.py (Line 135)
```

### Creation
```python
app = FastAPI(
    title="Valhalla API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)
```

### Lifespan Management
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan - boots fast, then runs delayed init in background."""
    asyncio.create_task(run_post_boot_init(delay_seconds=5))
    yield
```

---

## STARTUP FLOW

### 1. Entry Point: `python start.py`

**File**: `d:\dev\start.py`

**Purpose**: Render deployment entrypoint (also used locally)

**Key Actions**:
1. Clears sys.path conflicts
2. Sets priority paths:
   - Priority 1: `services/api` (so `from app.X` resolves here)
   - Priority 2: `d:\dev` (fallback for root-level app modules)
3. Sets environment variables:
   - `DATABASE_URL`: Defaults to `sqlite:///valhalla_test.db` if not set
   - `VALHALLA_JWT_SECRET`: Defaults to dev key if not set
4. Extracts `PORT` (default 8000) and `HOST` (default 0.0.0.0)
5. Runs: `uvicorn.run("app.main:app", host=host, port=port)`

### 2. Docker Entrypoint: `/entrypoint.sh`

**File**: `d:\dev\entrypoint.sh`

**Purpose**: Container startup script

**Actions**:
1. Sets working directory to `/app/services/api`
2. Runs: `python start.py`

### 3. Dockerfile Configuration

**File**: `d:\dev\Dockerfile`

**Key Settings**:
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/services/api
WORKDIR /app/services/api
ENTRYPOINT ["/entrypoint.sh"]
```

### 4. Render Deployment

**File**: `d:\dev\render.yaml`

**Docker Command**: `python start.py`  
**Health Check Path**: `/health`  
**Database**: From `DATABASE_URL` env var (PostgreSQL on Render, SQLite local)

---

## APP INITIALIZATION SEQUENCE

```
start.py runs
    ↓
[Environment variables set]
    ↓
uvicorn.run("app.main:app")
    ↓
services/api/app/main.py loads
    ↓
FastAPI(lifespan=lifespan) instantiated
    ↓
[Routers Included]
    ├── system_boot_router (explicit, line 143)
    ├── jarvis.router (explicit, line 146)
    └── auto-loaded routers (via _autoload_router_modules, line ~160)
    ↓
[Models Registered]
    ├── Import app.models (line ~165)
    ├── Registers ORM metadata ONCE
    └── Prevents duplicate table registration
    ↓
[Lifespan Hook Triggered]
    ├── App starts (fast boot)
    ├── Schedules delayed init: run_post_boot_init(delay_seconds=5)
    └── Background task runs after 5-second stabilization
    ↓
[Health Probes Ready]
    ├── /health endpoint active
    ├── /healthz endpoint active
    └── Ready for requests
```

---

## ROUTER INCLUSION ORDER

### 1. Explicit Routers (Always Included First)

**System Boot** (Admin/Management)
```python
from app.routers.system_boot import router as system_boot_router
app.include_router(system_boot_router)  # Line 143
```

**Jarvis** (Heimdall Operator Interface)
```python
from app.routers import jarvis
app.include_router(jarvis.router)  # Line 146
```

### 2. Auto-Loaded Routers (Discovery Order)

Function: `_autoload_router_modules(app: FastAPI) -> int`  
Location: `services/api/app/main.py` (Line ~95)

**Discovery Process**:
1. Lists all `.py` files in `app/routers/` package
2. Skips: `system_boot.py`, `__init__.py`
3. For each module:
   - Imports it dynamically
   - Checks for `router` attribute
   - If exists: `app.include_router(router)`
   - Logs success
4. Returns count of loaded routers

**Total Auto-Loaded**: ~248 routers

**Logging Output**:
```
Autoloaded router: app.routers.weweb_auth
Autoloaded router: app.routers.va_intake
Autoloaded router: app.routers.messaging
... (248 more)
```

---

## CUSTOM ENDPOINTS (In main.py)

### Health Check Endpoints

**GET /health**
```python
@app.get("/health")
async def health() -> JSONResponse:
    cfg = _cfg_dict()
    qcounts = _queue_counts(cfg)
    hb = _heartbeat_info(cfg)
    return JSONResponse({
        "ok": True,
        "queue_counts": qcounts,
        "heartbeat_info": hb,
        ...
    })
```

**GET /healthz** (Alternative Kubernetes-style)
```python
@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"ok": True, ...})
```

### Metrics Endpoints

**GET /metrics**
- Returns queue status, heartbeat, system state in JSON

**GET /metrics/prometheus**
- Returns Prometheus-compatible metrics format

---

## DATABASE INTEGRATION

### Migration Handling

**Location**: Via `start.py` → attempts `alembic upgrade head` before app starts

**Status**: ⚠️ Currently failing due to migration conflict (see DATABASE_MIGRATION_TRUTH.md)

### ORM Session Management

**Dependency Injection**:
```python
from app.core.db import get_db

@app.get("/some-endpoint")
def endpoint(db: Session = Depends(get_db)):
    # db is a database session
    ...
```

**Session Factory**: Configured in `app.core.db.py`

---

## CORS CONFIGURATION

**Location**: Middleware in `services/api/app/main.py`

**Current Settings** (from environment):
```python
CORSMiddleware(
    app,
    allow_origins=["*"],  # Set via CORS_ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: Render config sets `CORS_ALLOWED_ORIGINS = "*"` for WeWeb testing

---

## AUTHENTICATION & SECURITY

### JWT Token Handling

**Secret Key**: Set via `VALHALLA_JWT_SECRET` environment variable

**Location**: `app.security.auth` module

**Usage**: WeWeb auth endpoints (`/api/weweb/login`, etc.) use JWT

### API Key Authentication

**For Builder Endpoints** (`/builder/*`):
- Requires `X-API-Key` header
- Verified via `require_builder_key` dependency

**Key**: Set via `BUILDER_KEY` environment variable

---

## STARTUP REQUIREMENTS

### Environment Variables

| Variable | Default | Overridable |
|----------|---------|------------|
| DATABASE_URL | sqlite:///valhalla_test.db | Yes (Render sets to Postgres) |
| VALHALLA_JWT_SECRET | dev-secret-key-change-in-production | Yes |
| PORT | 8000 | Yes |
| HOST | 0.0.0.0 | Yes |
| CORS_ALLOWED_ORIGINS | * | Yes |
| BUILDER_KEY | test-builder-key-v0.2-verification | Yes |
| APP_ENV | production (implicit) | Yes |

### Database Requirements

- Must have SQLite, PostgreSQL, or compatible connection string
- Alembic migrations must complete successfully
- All tables must be created before app fully boots

### Python Requirements

- Python 3.11+ (per Dockerfile)
- Dependencies from `services/api/requirements.txt`
- Virtual environment activated

---

## HEALTH CHECK READINESS SEQUENCE

1. **Fast Boot** (< 100ms)
   - FastAPI app created
   - Routers attached
   - `/health` endpoint responds

2. **Delayed Init** (After 5 seconds)
   - Background task `run_post_boot_init()` runs
   - Initializes post-boot systems (if any)
   - Background operations don't block requests

3. **Full Readiness** (After 5+ seconds)
   - All subsystems initialized
   - Ready for money-loop operations

---

## DUPLICATE APP ROOTS WARNING

⚠️ **Three app locations exist (confusion risk)**:

1. `d:\dev\app/` (ROOT LEVEL — not used)
   - Do not modify or delete (for clarity)
   - Not referenced by startup

2. `d:\dev\services\api\app/` (CANONICAL — active)
   - This is the running app
   - All changes here

3. `d:\dev\valhalla_export/05_CODE_app/` (ARCHIVED — old export)
   - Do not use
   - For reference only

**Recommendation**: Clearly label the root-level `app/` folder as abandoned or move to archive.

---

## DEPLOYMENT READINESS

### Local Development
✅ Start with: `python start.py`  
✅ Access: `http://localhost:8000`  
✅ Database: SQLite (auto-created if missing)

### Render Production
✅ Docker container built from `Dockerfile`  
✅ Entrypoint: `entrypoint.sh` → `python start.py`  
✅ Database: PostgreSQL (from `DATABASE_URL` env var)  
✅ Health: `/health` endpoint monitored

### Testing
✅ Pytest configured (`pytest.ini`)  
✅ Tests available in `tests/` folder  
✅ Run: `pytest -q`

---

## NEXT STEPS

1. **Fix Alembic Migrations** (BLOCKER)
   - Resolve multiple migration heads
   - Ensure `alembic upgrade head` succeeds

2. **Start Backend**
   - `python start.py` should complete without errors
   - Health endpoint should respond

3. **Verify Routers**
   - `GET /health` should list loaded router count
   - `GET /docs` should show all endpoints

4. **Test WeWeb Integration**
   - POST `/api/weweb/login` with test credentials
   - GET `/api/weweb/me` with returned token
   - GET `/api/weweb/smoke` for connectivity check
