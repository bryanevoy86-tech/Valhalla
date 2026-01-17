# Valhalla Project - Complete Handover Document

**Generated:** December 4, 2025  
**Location:** `c:\dev\valhalla\`  
**Environment:** Windows PowerShell  
**Main Entry Point:** `services/api/main.py` (976 lines)

---

## 🎯 Quick Summary

**Valhalla** is a modular FastAPI platform with **92 routers** (70+ feature-flagged), autonomous AI (Heimdall), semantic search, and full observability stack.

**Key Facts:**
- Python 3.10+, FastAPI 0.115.0, Pydantic v2, SQLAlchemy 2.0
- 11-service Docker stack (API, Postgres, Heimdall, Prometheus, Grafana, Tempo, Vector, OTEL, Alertmanager, Blackbox, Ngrok)
- Graceful degradation: routers load with try/except (missing deps don't crash)
- Deployed on Render.com with auto-deploy from GitHub
- 40+ README docs for features

---

## 📁 File Structure

```
valhalla/
├── services/api/              # PRIMARY APPLICATION (976-line main.py)
│   ├── main.py                # FastAPI app entry, imports 70+ routers
│   ├── app/
│   │   ├── routers/           # 92 router files (health, grants, research, builder, etc.)
│   │   ├── models/            # SQLAlchemy 2.0 models
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   ├── core/              # config.py, db.py, settings.py, git_utils.py, embedding_utils.py
│   │   ├── telemetry/         # OpenTelemetry middleware
│   │   └── metrics/           # Prometheus middleware
│   ├── alembic/versions/      # DB migrations (v3_4_embeddings.py, etc.)
│   ├── export_worker.py       # Async job runner
│   ├── requirements.txt       # 22 Python packages
│   └── Dockerfile
│
├── backend/                   # LEGACY (mostly unused)
│   ├── main.py                # 510 lines - Heimdall admin routes only
│   └── routes/                # 4 legacy files (exports, progress, uploads, webhooks)
│
├── app/main.py                # MINIMAL STUB (3 lines, health check)
│
├── frontend/                  # Next.js UI (minimal wiring)
│
├── ops/                       # Observability configs
│   ├── prometheus/            # prometheus.yml, rules.yml, alerts.yml
│   ├── grafana/, vector/, tempo/, otel-collector/, alertmanager/, blackbox/
│
├── heimdall/                  # AI agent files
├── tools/auto_build.py        # Auto-builder script
├── docker-compose.yml         # 177 lines, 11 services
├── pyproject.toml             # black, isort, ruff, mypy config
├── requirements.txt           # Root deps (same 22 packages)
└── 40+ README.*.md files      # Feature docs
```

---

## 🛠️ Tech Stack

**Python Packages (from `requirements.txt`):**
```
sentry-sdk, boto3
fastapi==0.115.0, uvicorn==0.30.6, gunicorn==21.2.0
pydantic==2.9.2, pydantic-settings==2.4.0
httpx==0.27.2, requests==2.32.3
PyYAML==6.0.2, Jinja2==3.1.4
psycopg2-binary==2.9.11, sqlalchemy==2.0.35, alembic==1.13.2
python-slugify==8.0.4, python-multipart==0.0.6
loguru==0.7.0, feedparser==6.0.11, beautifulsoup4==4.12.3
APScheduler==3.10.4, GitPython==3.1.43
```

**Code Standards (from `pyproject.toml`):**
- Black: line-length 100, Python 3.10+
- Isort: black profile
- Ruff: E, F, I, UP, B, SIM, W, Q
- Mypy: strict, no untyped defs

**Docker Services (from `docker-compose.yml`):**
1. **api** - FastAPI (port 8000)
2. **db** - PostgreSQL 16 (port 5432, user/pass/db = valhalla)
3. **heimdall** - Python 3.11-slim, sleep infinity, mounted to /app
4. **prometheus** - v2.54.1 (port 9090)
5. **grafana** - v11.2.0 (port 3000, plugins: piechart, worldmap)
6. **alertmanager** - v0.27.0 (port 9093)
7. **vector** - v0.43.0-debian (port 8686, log shipping)
8. **tempo** - v2.5.0 (port 3200, tracing)
9. **otel-collector** - v0.101.0 (ports 4317, 4318)
10. **blackbox** - v0.25.0 (port 9115, HTTP monitoring)
11. **ngrok** - latest (port 4040 UI, tunnels api:8000)

---

## 📋 Complete Router List (92 files)

**Core Routers (Always Available):**
- health.py, metrics.py, capital.py, telemetry.py, admin.py
- ui_dashboard.py, system_health.py, analytics.py, alerts.py, roles.py

**Feature Routers (Conditional via try/except in main.py):**
- accounting.py, admin_build.py, admin_handoff.py, admin_logs.py, admin_ops.py, admin_privacy.py, admin_secscan.py
- advanced_negotiation_techniques.py, agreements.py, agreements_upload.py
- arbitrage.py, audit.py
- behavior.py, behavioral_profiles.py, blackice.py, brrrr.py
- builder.py, buyers.py, buyer_match.py
- children.py, closers.py, closer_engine.py, compliance.py
- contracts.py, contract_engine.py
- deals.py, deal_analyzer.py, disputes.py, docs.py
- encryption.py, exports_upload.py
- features.py, finops.py, freeze.py
- god_arbitration.py, god_cases.py, god_verdicts.py, grants.py
- heimdall_training.py
- influence.py, intake.py, integrity.py
- jobs.py
- king.py, knowledge.py
- languages.py, lawyer_feed.py, leads.py, leads_status.py, legal.py
- logging.py, loki.py
- match.py, messaging.py
- negotiations.py, negotiation_strategies.py, neg_enhance.py, notifications.py, notify.py
- orchestrator.py
- pantry.py, payments.py, playbooks.py, policies.py, providers.py
- queen.py
- rbac.py, reports.py, research.py, research_semantic.py, resort.py
- scheduled_jobs.py, security.py, specialists.py, specialist_feedback.py, sync_engine.py
- tax_bridge.py, tax_tracker.py, title.py
- underwriter.py, users.py
- workflows.py

**Legacy Backend Routes (4 files in `backend/routes/`):**
- exports.py, progress.py, uploads.py, webhooks.py

---

## 🚀 Development Workflow (from `DEV_WORKFLOW.md`)

### Local Setup (Windows PowerShell)

```powershell
# 1. Create venv & install
cd "c:\dev\valhalla"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r services\api\requirements.txt

# 2. Run dev server (foreground with auto-reload)
.\.venv\Scripts\python.exe -m uvicorn valhalla.services.api.main:app --reload --port 4000

# 3. Test endpoints
Invoke-RestMethod http://127.0.0.1:4000/api/health | ConvertTo-Json -Depth 5
```

### Docker Stack

```powershell
# Start all services
docker compose up --build

# Services available:
# - API: http://localhost:8000
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
# - Ngrok UI: http://localhost:4040
# - DB: localhost:5432 (user: valhalla, pass: valhalla)
```

### Key Endpoints (from `README.md`)

```bash
# Health check
GET /api/v1/health/live → {"status":"ok"}

# OpenAPI docs
GET /api/v1/openapi.json

# Debug routes (see all registered routers & availability flags)
GET /debug/routes

# Example protected route
curl -H "token: <ACCESS_TOKEN>" http://localhost:8000/api/v1/leads?limit=10
```

---

## 🤖 Heimdall AI System

### 1. Semantic Search (from `HEIMDALL_SEMANTIC_WORKFLOW.md` - 509 lines)

**Flow:**
1. **Ingest**: `POST /api/research/ingest` → stores docs in DB
2. **Embed (external)**: Compute vectors via OpenAI/Cohere
3. **Store**: `POST /api/research/embeddings/upsert` → save vectors
4. **Query**: User asks question → embed query with same model
5. **Search**: `POST /api/research/semantic_query` → cosine similarity
6. **Ground**: Use top results to inform Builder tasks

**Key Endpoints:**
- `/research/ingest` - Fetch & parse docs
- `/research/embeddings/upsert` - Store doc vectors
- `/research/semantic_query` - Find similar docs
- `/research/embeddings/stats` - Check coverage

### 2. Auto-Builder (from `AUTO_BUILDER_GUIDE.md` - 421 lines)

**What it does:** AI agents programmatically create/modify code through Builder API.

**Flow:**
1. Register agent: `POST /api/builder/register`
2. Create task: `POST /api/builder/tasks`
3. Upload drafts: `POST /api/builder/draft?task_id=X`
4. Dry-run: `POST /api/builder/apply` (approve=false)
5. Apply: `POST /api/builder/apply` (approve=true)

**Safety:**
- Whitelist in `config.py`: `BUILDER_ALLOWED_DIRS` (routers, models, schemas, main.py, etc.)
- Max file size: 200KB
- Git integration: auto-commit if `GIT_ENABLE_AUTOCOMMIT=true`

**Script:** `tools/auto_build.py` orchestrates full builds

**GitHub Actions:** `.github/workflows/auto-builder.yml` (manual trigger + daily 3:30 AM Winnipeg)

### 3. Admin Routes (from `backend/main.py` - 510 lines)

These are **Heimdall-specific admin endpoints**:
- `/admin/heimdall/api/autopr/status` - Auto-PR status
- `/admin/heimdall/autopr/run` - Trigger PR job
- `/admin/heimdall/api/alerts/status` - Alert system status
- `/admin/heimdall/api/alerts/test` - Test Discord notifications

---

## 📚 Documentation Files (40+)

**Core Guides:**
- `AI_GUIDE.md` (159 lines) - Engineering brief for AI agents
- `DEV_WORKFLOW.md` (61 lines) - Daily dev workflow
- `AUTO_BUILDER_GUIDE.md` (421 lines) - Auto-builder system
- `HEIMDALL_SEMANTIC_WORKFLOW.md` (509 lines) - Semantic search architecture
- `TESTING.md`, `RESEARCH_CORE_SETUP.md`

**Infrastructure:**
- `README.health.md`, `README.metrics.md`, `README.telemetry.md`
- `README.logging.md`, `README.alerts.md`, `README.alerts_auto.md`
- `README.ci.md`, `README.dashboard.md`, `README.ui_dashboard.md`

**Features (in `services/api/`):**
- `README.leads.md`, `README.messaging.md`, `README.negotiations.md`
- `README.negotiation_strategies.md`, `README.notifications.md`
- `README.payments.md`, `README.rbac.md`, `README.users.md`
- `README.advanced_negotiation.md`, `README.behavioral_profiling.md`
- `README.deal_analyzer.md`, `README.influence.md`
- `README.languages.md`, `README.pack75_76.md`, `README.pack81_85.md`

**Deployment:**
- `RENDER_CREDENTIALS.md`, `CAPITAL_METRICS_DEPLOYMENT.md`
- `render.yaml`

---

## 🎓 Code Standards (from `AI_GUIDE.md` - 159 lines)

### Non-Negotiables
1. **Fix runtime errors before refactors**
2. **Keep public API routes stable** unless asked
3. **Add Alembic migrations** for all DB schema changes (no ad-hoc drift)

### Code Style
- **Indentation**: 4 spaces, no tabs
- **Python**: 3.10+, type hints, async/await
- **Imports**: Add missing, remove dead code
- **Logging**: Use loguru/logging, not `print()`
- **Types**: Prefer `Annotated` for FastAPI dependencies

### Auto-Fixers
- Black: line-length 100
- Isort: black profile
- Ruff: auto-fix on save
- Mypy: strict mode

### Common Fixes to Apply Automatically
- Indentation/async misuse in workers
- Missing imports / dead code
- Type errors
- Bare prints → logging
- Ensure migrations for new DB columns

---

## 🔧 Key Configuration

**Environment Variables (from `docker-compose.yml`):**
```bash
DATABASE_URL=postgresql://valhalla:valhalla@db:5432/valhalla
HEIMDALL_BUILDER_API_KEY=test123  # or real key
NGROK_AUTHTOKEN=<your_token>
PYTHONUNBUFFERED=1

# Heimdall
GIT_AUTHOR_NAME="Heimdall Bot"
DISCORD_WEBHOOK_URL=<webhook>
GITHUB_TOKEN=<token>

# Grafana
GF_SECURITY_ADMIN_PASSWORD=<password>

# Vector
VECTOR_ENABLED=true
VECTOR_S3_ENABLE=true/false
VECTOR_OS_ENABLE=true/false
```

**Settings Location:**
- `services/api/app/core/settings.py` (Pydantic settings)
- `services/api/app/core/config.py` (BUILDER_ALLOWED_DIRS, file size limits)

---

## 🚨 Architecture Notes

### Graceful Degradation Pattern (from `main.py`)

Every feature router uses this pattern:
```python
try:
    from app.routers.grants import router as grants_router
    GRANTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import grants router: {e}")
    grants_router = None

# Later...
if GRANTS_AVAILABLE and grants_router is not None:
    app.include_router(grants_router, prefix="/api")
```

**Consequence:** You can't tell from code inspection which routers are actually loaded. Use `GET /debug/routes` to see runtime status.

### Dual Backend Confusion

**TWO main.py files exist:**
1. `services/api/main.py` (976 lines) - **PRIMARY APP** with 70+ routers
2. `backend/main.py` (510 lines) - **LEGACY** Heimdall admin routes only
3. `app/main.py` (3 lines) - Minimal stub

**Recommendation:** Consolidate `backend/main.py` routes into `services/api/app/routers/admin_*.py` and deprecate backend/.

### Database Locations

**THREE Alembic setups:**
1. `alembic/` (root level) - older migrations?
2. `services/api/alembic/` - **PRIMARY** migrations (v3_4_embeddings.py)
3. Settings: `services/api/alembic.ini`

**Recommendation:** Verify which is active, consolidate to one location.

---

## 🧪 Testing

**Test Files:**
- `test_builder_api.py`, `test_telemetry.py`, `run_health_test.py`
- `services/api/tests/` - pytest suite (test_grants.py, test_health.py, test_reports.py, etc.)

**Run Tests:**
```powershell
# In Docker
docker compose exec api pytest -q app/tests

# Local
pytest services/api/tests/
```

---

## 📊 Monitoring & Observability

**Stack:**
- **Prometheus** (http://localhost:9090) - Metrics collection
- **Grafana** (http://localhost:3000) - Dashboards
- **Tempo** (http://localhost:3200) - Distributed tracing
- **Vector** (http://localhost:8686) - Log aggregation → S3 or OpenSearch
- **OTEL Collector** (ports 4317, 4318) - Telemetry ingestion
- **Alertmanager** (http://localhost:9093) - Alert routing
- **Blackbox** (http://localhost:9115) - Endpoint monitoring

**Middleware (from `main.py`):**
```python
from app.telemetry.middleware import TelemetryExceptionMiddleware
from app.metrics.middleware import MetricsMiddleware

app.add_middleware(TelemetryExceptionMiddleware)  # OpenTelemetry
app.add_middleware(MetricsMiddleware)  # Prometheus
```

---

## 🔄 CI/CD

**GitHub Actions:**
- Auto-builder workflow: manual trigger + daily 3:30 AM
- Auto-PR system: `scripts/ci/auto_pr.py`
- Status: `dist/docs/auto_pr_status.json`

**Render Deployment:**
- Auto-deploy from GitHub pushes
- Uses `render.yaml` for service config
- Production DB: Postgres (auto-configured via DATABASE_URL)

---

## 🎯 Current State & Challenges

### What's Working
✅ Core health/metrics/telemetry endpoints  
✅ Heimdall semantic search & auto-builder  
✅ Full observability stack (Prometheus, Grafana, Tempo)  
✅ Docker stack with 11 services  
✅ Graceful degradation (missing routers don't crash)  
✅ Render deployment with auto-deploy  

### Known Issues / Complexity
⚠️ **70+ conditional routers** - hard to know what's actually loaded  
⚠️ **Multiple main.py files** - `services/api/`, `backend/`, `app/` - confusing  
⚠️ **Dual Alembic locations** - root vs services/api  
⚠️ **Legacy backend/** code - mostly unused, should deprecate  
⚠️ **Import failures silent** - try/except hides broken routers  

### Recommendations for Next AI
1. **Check `/debug/routes`** to see actual loaded routers before debugging
2. **Focus on `services/api/main.py`** as primary entry point
3. **Consolidate backends** - merge backend/main.py into services/api/app/routers/
4. **Migration audit** - verify which Alembic location is active
5. **Add router health checks** - surface import errors better

---

## 📝 Quick Reference Commands

### Start Services
```powershell
# Docker (full stack)
docker compose up --build

# Local API only
.\.venv\Scripts\python.exe -m uvicorn valhalla.services.api.main:app --reload --port 4000
```

### Database
```powershell
# Connect to Postgres
docker compose exec db psql -U valhalla -d valhalla

# Run migrations
docker compose exec api alembic upgrade head
```

### Health Checks
```powershell
# API health
Invoke-RestMethod http://localhost:8000/api/health

# See loaded routers
Invoke-RestMethod http://localhost:8000/debug/routes | ConvertTo-Json -Depth 10
```

### Monitoring URLs
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Ngrok UI: http://localhost:4040
- Vector: http://localhost:8686
- Tempo: http://localhost:3200

---

## 🔐 Security & Keys

**Where Secrets Go:**
- `HEIMDALL_BUILDER_API_KEY` - Builder API auth (default: test123)
- `NGROK_AUTHTOKEN` - Ngrok tunnel auth
- `GITHUB_TOKEN` - Git automation
- `DISCORD_WEBHOOK_URL` - Alert notifications
- `GF_SECURITY_ADMIN_PASSWORD` - Grafana admin
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - S3 for Vector

**Never commit:** `.env` files with real secrets

---

## 💡 For Another AI Taking Over

**Read These First:**
1. `AI_GUIDE.md` - Engineering principles & non-negotiables
2. `DEV_WORKFLOW.md` - How to run locally
3. `services/api/main.py` - Understand router loading pattern
4. Hit `GET /debug/routes` - See what's actually loaded

**Key Insights:**
- **92 routers exist**, but most are feature-flagged (try/except imports)
- **Graceful degradation** means import failures are silent warnings
- **Heimdall** is an autonomous AI with semantic search + auto-builder
- **Full observability** is built-in (Prometheus, Grafana, Tempo, Vector)
- **Docker stack is complex** (11 services) but well-documented

**Common Tasks:**
- Add new router: Create in `app/routers/`, add try/except import to `main.py`
- DB change: Create Alembic migration in `services/api/alembic/versions/`
- Deploy: Push to GitHub → Render auto-deploys
- Monitor: Check Grafana dashboards

**Watch Out For:**
- Silent import failures (check `/debug/routes` not just code)
- Multiple `main.py` files (use `services/api/main.py`)
- Dual Alembic locations (use `services/api/alembic/`)

---

**End of Handover**

Generated from: `c:\dev\valhalla\`  
Primary docs: AI_GUIDE.md, DEV_WORKFLOW.md, AUTO_BUILDER_GUIDE.md, HEIMDALL_SEMANTIC_WORKFLOW.md  
Questions? Check the 40+ README files or hit `/debug/routes` to see runtime state.
