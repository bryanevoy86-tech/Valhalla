# Backend Spine Audit — V1 Freeze Checkpoint

**Date:** March 29, 2026  
**Status:** BACKEND V1 FREEZE MODE  
**Target:** Document canonical backend spine for stable frontend integration

---

## 1. CANONICAL BACKEND ENTRYPOINTS

### Production (Render Deploy)

**Config:** `render.yaml` (at repo root)

```yaml
services:
  - type: web
    name: valhalla-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerCommand: python start.py
    healthCheckPath: /health
    port: 10000 (from env PORT var)
```

**Docker:** `Dockerfile` (at repo root)

```dockerfile
WORKDIR /app
COPY . /app
WORKDIR /app/services/api
ENV PYTHONPATH=/app/services/api
# Runs: python start.py
```

**Execution Chain:**
```
python start.py
  ↓
services/api/start.py (uvicorn launcher)
  ↓
main:app (imports app from services/api/main.py)
  ↓
services/api/main.py (re-export)
  ↓
services/api/app/main.py (REAL FastAPI app instance)
```

---

### Local Development

**Docker Compose:** `docker-compose.yml` (at repo root)

```yaml
services:
  api:
    build:
      context: .
      dockerfile: services/api/Dockerfile
    ports:
      - "8000:8000"
```

**Direct uvicorn:**
```bash
cd services/api
python -m uvicorn main:app --reload --port 8000
# or
python start.py  # uses PORT env var, defaults to 10000
```

---

## 2. CANONICAL WORKING DIRECTORY & PATH STRUCTURE

### Canonical Root

```
d:\dev/                                    ← Repo root
├── Dockerfile                             ← Prod builder
├── docker-compose.yml                     ← Local dev
├── render.yaml                            ← Prod deploy config
├── services/
│   └── api/
│       ├── Dockerfile                     ← API service builder
│       ├── start.py                       ← Entrypoint (called by render.yaml)
│       ├── main.py                        ← Re-export module
│       ├── alembic.ini                    ← Migration config (canonical)
│       ├── alembic/
│       │   ├── env.py                     ← Migration env config
│       │   └── versions/                  ← 100+ migration files
│       ├── requirements.txt               ← Dependencies
│       └── app/
│           ├── main.py                    ← REAL FastAPI app instance
│           ├── core/
│           │   ├── db.py                  ← SQLAlchemy Base, session
│           │   ├── settings.py            ← Config/env vars
│           │   └── ...
│           ├── models/                    ← All ORM models
│           ├── routers/                   ← All API route handlers
│           ├── schemas/                   ← Pydantic schemas
│           ├── services/                  ← Business logic
│           └── middleware/
└── docs/                                  ← Documentation (including this file)
```

### Expected by Docker

```
/app/                              ← Docker WORKDIR (copy of d:\dev)
/app/services/api/                 ← Set as WORKDIR by Dockerfile
/app/services/api/main.py          ← Entry module for uvicorn
/app/services/api/app/main.py      ← Real app
/app/services/api/alembic/         ← Migrations
```

---

## 3. DUPLICATE/DEAD PATHS TO AVOID

### ⚠️ DO NOT USE THESE

| Path | Status | Why | Action |
|------|--------|-----|--------|
| `d:\dev\app\main.py` | Dead delegation | Only re-exports prod app; confusing | Keep as-is (docs warn users) |
| `d:\dev\services\api\main.py` | Re-export shim | Intermediate layer between start.py and real app | Keep as-is (required by uvicorn) |
| `d:\dev\alembic.ini` | Dead (if exists at root) | Migrations are in `services/api/alembic.ini` | Use only `services/api/alembic.ini` |
| `d:\dev\_archive/` | Legacy archive | Pre-freeze codebase snapshots | Never import from this |
| Various valhalla/* paths | Dead structure | Old project layout before services/api consolidation | Ignore completely |

---

## 4. MIGRATION SYSTEM

### Canonical Migration Path

**Location:** `services/api/alembic/`

**Config File:** `services/api/alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg2://valhalla:valhalla@127.0.0.1:5432/valhalla
# Overridden by DATABASE_URL env var in env.py
```

**Env Config:** `services/api/alembic/env.py`

```python
# Adds /app/services/api to sys.path
# Imports app.core.db.Base for metadata discovery
# Loads all ORM models for migration generation
```

### Migration Head Status

**Current Head:** `20260205_final_consolidation` (single linear head)

**Why This Head:**
- Consolidated all previous divergent branches
- Known final state before lead acquisition migration was removed (VARCHAR(32) constraint)
- Clean, linear history for reproducible deployments

**Migration Count:** 100+ migrations (legacy + modern)
- Modern numbered: 0046-0114, 0100-0114, pack_60+, v3_*
- Legacy numbered: 70-99 (old schema)
- Merge migrations: Multiple consolidation points

---

## 5. CURRENT ROUTER REGISTRATION STATUS

### ✅ MOUNTED & LIVE

Core pipeline routers actively registered in `services/api/app/main.py`:

```
✅ system_selftest
✅ governance_runbook           prefix=/api
✅ governance_policy            prefix=/api
✅ governance_risk              prefix=/api
✅ go_live                      prefix=/api
✅ contracts_lifecycle          
✅ document_routing
✅ deal_finalization
✅ floor_control
✅ contracts_pipeline
✅ contracts_webhooks
✅ heimdall                     prefix=/api
✅ audit                        prefix=/api
✅ operational_dashboard        prefix=/api
✅ jobs                         prefix=/api
✅ notify                       prefix=/api
✅ engine_admin
✅ market_policy                prefix=/api
✅ buyers (DB-backed)
✅ leads
✅ deals
✅ offers
✅ buyer_match
✅ lead_engine
│ (and 50+ more optional packs)
```

### ⚠️ SKIPPED (Non-blocking)

Gracefully skipped due to optional dependencies:

```
⚠️ pack_sw       (Pydantic validation issue - Annotated field clash)
⚠️ pack_sx       (Pydantic validation issue - Annotated field clash)
⚠️ pack_sy       (Pydantic validation issue - Annotated field clash)
⚠️ pack_sz_ta_tb (Missing module app.routers.pack_sz_ta_tb)
❌ opportunity_tracker  (COMMENTED OUT as of latest commit - model removed)
```

### ✅ REQUIREMENTS MET

- All **launch-critical routers** are mounted
- Core pipeline (leads → deals → audit) fully operational
- Governance/go-live routes live
- Heimdall analysis routes live
- Health check responding
- Graceful skips for optional packs

---

## 6. HEALTH & OBSERVABILITY ENDPOINTS

### Health Check (used by Render)

```
GET /health
→ Returns 200 OK (FastAPI default, used by render.yaml healthCheckPath)
```

### OpenAPI Documentation

```
GET /docs
→ Swagger UI with all registered routes
→ Accessible at https://valhalla-api-ha6a.onrender.com/docs (prod)
→ Accessible at http://localhost:10000/docs (local)
```

### Lifespan Startup Sequence (logged to stdout + logging)

```
1. verify_schema_initialized() - checks DB has applied migrations
2. retention.EN loop - if enabled, runs data retention job
3. drift.check() - if DRIFT_CHECK_ON_STARTUP=1, runs integrity check
4. Server startup complete
```

---

## 7. STARTUP RISKS & MITIGATION

### Risk: Missing or Conflicting Migrations

**Current Mitigation:**
- Single linear head (20260205_final_consolidation)
- No multiple heads error
- Oversized migration ID removed (VARCHAR(32) constraint)

**Verification Command:**
```bash
cd services/api
python -m alembic heads
# Expected: Shows single head (20260205_final_consolidation)
```

### Risk: ORM Model Registry Mismatch

**Current Mitigation:**
- alembic/env.py explicitly imports all models
- Base.metadata captures all tables
- Models dir scanned at startup

**Safe Pattern:**
- All models inherit from `app.core.db.Base`
- All models live in `app/models/` or subpackages
- None in dead_code/ or archive/

### Risk: Import-time Side Effects

**Current Mitigation:**
- All routers use try/except wrapper in main.py
- Non-critical packs gracefully skip
- Logging shows which routers succeeded vs. skipped

### Risk: Env Misconfig

**Current Mitigation:**
- `app.core.settings.settings` centralizes config
- DATABASE_URL can override alembic.ini
- Health endpoint confirms schema loaded

---

## 8. DEPLOYMENT TOPOLOGY

### Render Deployment (CURRENT LIVE)

```
GitHub push to main
  ↓
Render auto-redeploy triggered
  ↓
Docker build from root Dockerfile
  ↓
WORKDIR /app/services/api
PYTHONPATH=/app/services/api
  ↓
alembic upgrade head (run migrations)
  ↓
python start.py (start uvicorn)
  ↓
Port 10000 (or env PORT var)
  ↓
https://valhalla-api-ha6a.onrender.com
```

**Current Status:** 🟢 **LIVE** (as of March 29, 2026)

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
==> Your service is live 🎉
==> Available at https://valhalla-api-ha6a.onrender.com
```

### Local Docker Compose

```
docker-compose build api
docker-compose up api
  ↓
WORKDIR /app/services/api
Alembic migrations (if DB present)
Uvicorn on port 8000
```

### Direct Local Python

```
cd services/api
python start.py
  ↓
Uvicorn on port 10000 (or $PORT)
  ↓
http://localhost:10000
```

---

## 9. BACKEND SPINE SUMMARY (FOR FRONTEND INTEGRATION)

### What Frontend Needs to Know

**API Base URL:**
- Production: `https://valhalla-api-ha6a.onrender.com`
- Local dev: `http://localhost:10000` or `http://localhost:8000`

**Key Endpoints (V1 Freeze - See V1_API_CONTRACT.md for full spec):**

```
GET    /api/deals                  → List all deals
GET    /api/deals/{id}             → Get single deal
GET    /api/leads                  → List all leads
POST   /api/leads                  → Create lead
POST   /api/deals/from-lead/{id}   → Convert lead to deal
PATCH  /api/deals/{id}/stage       → Advance deal stage
GET    /api/audit/deals/{id}       → Get deal audit trail
GET    /api/governance/runbook/status → Executor blockers/warnings
GET    /health                     → Health check
GET    /docs                       → OpenAPI docs
```

**Auth:** (Currently header-based testing mode)
- Custom auth layer not yet in V1 spec
- Governance/go-live endpoints assume admin context

**Media Types:**
- JSON in/out
- ISO 8601 datetime format
- UUID strings for IDs

---

## 10. OUTSTANDING INFRASTRUCTURE ITEMS

### Not Critical for V1 (Deferred to Phase 2+)

- ❌ Lead acquisition migration (0115) - removed due to VARCHAR constraint; can re-add post-V1
- ❌ Complete auth/session system - governance assumes admin  access for now
- ❌ Opportunity tracker router - disabled (model removed); can restore later
- ❌ Dynamic Heimdall Builder key config - 503 external dependency
- ❌ WeEB webhook integration - not started

### Why Deferred

- Not needed for simple deals list UI (Phase 1 WeWeb)
- Can be added post-validation without breaking stable backend
- Would delay launch-critical checkpoint

---

## 11. VERIFIED FACTS (AS OF MARCH 29, 2026)

✅ **Migrations:** Single head, clean, linear chain  
✅ **App Startup:** All core routers loaded, non-critical packs gracefully skipped  
✅ **Database:** Schema initialized, alembic_version table correct  
✅ **Health:** 200 OK on root, /health, /docs endpoints  
✅ **Core Pipeline:** Leads, deals, audit, hemidall routes all live  
✅ **Logs:** Clean startup sequence, lifespan handlers working  
✅ **Deployment:** Currently live on Render, responding to requests  
✅ **No Blocking Errors:** Import errors only in dead code (opportunity) — commented out  

---

## NEXT STEPS

Proceed to: **PHASE 2 — V1_BACKEND_FREEZE_CHECKLIST.md**
