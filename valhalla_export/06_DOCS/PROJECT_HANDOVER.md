# Valhalla Project - Complete Handover Document

**Generated:** December 4, 2025  
**Location:** `c:\dev\valhalla\`  
**Environment:** Windows PowerShell  
**Main API Entry:** `services/api/main.py` (976 lines, FastAPI 3.4)

---

## 🎯 Executive Summary

**Valhalla** is a modular FastAPI platform with **70+ feature-flagged routers**, semantic AI capabilities, and full observability. Key characteristics:

- **Graceful Degradation**: Routers load via try/except; missing dependencies don't crash the app
- **Heimdall AI**: Autonomous agent with semantic search, auto-builder, and research capabilities  
- **Full Observability**: Prometheus, Grafana, Tempo, Vector, OpenTelemetry integrated
- **Docker Stack**: 8 services (API, DB, Heimdall, Prometheus, Grafana, Alertmanager, Vector, Tempo, OTEL, Blackbox, Ngrok)
- **Deployment**: Render.com with auto-deploy from GitHub

---

---

## 📁 Project Structure

```
valhalla/
├── services/api/                       # PRIMARY APPLICATION
│   ├── main.py                         # 976 lines - FastAPI app with 70+ routers
│   ├── app/
│   │   ├── routers/                    # 92 router files (see full list below)
│   │   │   ├── health.py, metrics.py, capital.py, telemetry.py, admin.py
│   │   │   ├── grants.py, buyers.py, deals.py, contracts.py, match.py
│   │   │   ├── research.py, research_semantic.py, playbooks.py, jobs.py
│   │   │   ├── builder.py, reports.py  # Auto-builder & reporting
│   │   │   └── [87 more routers...]
│   │   ├── models/                     # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/                    # Pydantic v2 schemas
│   │   ├── core/
│   │   │   ├── config.py              # BUILDER_ALLOWED_DIRS whitelist
│   │   │   ├── db.py                  # Database engine & session
│   │   │   ├── settings.py            # Pydantic settings (env vars)
│   │   │   ├── dependencies.py        # FastAPI dependencies
│   │   │   ├── git_utils.py           # Git automation for builder
│   │   │   └── embedding_utils.py     # Embedding helpers
│   │   ├── telemetry/                 # OpenTelemetry middleware
│   │   └── metrics/                   # Prometheus metrics
│   ├── alembic/                       # Database migrations
│   │   └── versions/                  # Migration files (v3_4_embeddings.py, etc.)
│   ├── export_worker.py               # Async job runner
│   ├── requirements.txt               # Python deps (22 packages)
│   └── Dockerfile                     # API container image
│
├── backend/                           # LEGACY CODE (mostly unused)
│   ├── main.py                        # 510 lines - Heimdall admin routes
│   └── routes/                        # 4 legacy routes
│       ├── exports.py, progress.py, uploads.py, webhooks.py
│
├── app/                               # MINIMAL STUB
│   └── main.py                        # 3-line health check stub
│
├── frontend/                          # NEXT.JS UI (minimal wiring)
│   ├── App.jsx, next.config.js, package.json
│
├── ops/                               # OBSERVABILITY CONFIG
│   ├── prometheus/                    # prometheus.yml, rules.yml, alerts.yml
│   ├── grafana/                       # Dashboards & datasources
│   ├── vector/                        # vector.yaml (log shipping)
│   ├── tempo/                         # tempo.yaml (tracing backend)
│   ├── otel-collector/                # config.yaml (OTEL collector)
│   ├── alertmanager/                  # alertmanager.yml
│   └── blackbox/                      # blackbox.yml (endpoint monitoring)
│
├── heimdall/                          # AI AGENT FILES
├── tools/                             # AUTOMATION SCRIPTS
│   └── auto_build.py                  # Auto-builder script (see AUTO_BUILDER_GUIDE.md)
│
├── alembic/                           # ROOT MIGRATIONS (dual location)
├── docker-compose.yml                 # 177 lines - 11 services
├── pyproject.toml                     # Black, isort, ruff, mypy config
├── requirements.txt                   # Root-level deps (22 packages)
└── [40+ README files]                 # Feature docs (see list below)
```

### Complete Router List (92 files in `services/api/app/routers/`)

**Core (Always Available):**
- health.py, metrics.py, capital.py, telemetry.py, admin.py
- ui_dashboard.py, system_health.py, analytics.py, alerts.py, roles.py

**Feature Routers (Conditional Load via try/except):**
- accounting.py, admin_build.py, admin_handoff.py, admin_logs.py, admin_ops.py
- admin_privacy.py, admin_secscan.py, advanced_negotiation_techniques.py
- agreements.py, agreements_upload.py, arbitrage.py, audit.py
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

---

---

## 🛠️ Tech Stack (Actual Dependencies)

### Core Python (`requirements.txt` - 22 packages)
```
sentry-sdk                    # Error tracking
boto3                         # AWS SDK
fastapi==0.115.0              # Web framework
uvicorn==0.30.6               # ASGI server
uvicorn[standard]==0.30.6     # With websockets support
gunicorn==21.2.0              # Production server
pydantic==2.9.2               # Data validation (v2!)
pydantic-settings==2.4.0      # Settings management
httpx==0.27.2                 # HTTP client
PyYAML==6.0.2                 # YAML parsing
Jinja2==3.1.4                 # Templating
psycopg2-binary==2.9.11       # PostgreSQL driver
sqlalchemy==2.0.35            # ORM (v2!)
alembic==1.13.2               # Migrations
python-slugify==8.0.4         # URL slugs
python-multipart==0.0.6       # File uploads
loguru==0.7.0                 # Logging
feedparser==6.0.11            # RSS parsing
beautifulsoup4==4.12.3        # HTML parsing
requests==2.32.3              # HTTP (legacy)
APScheduler==3.10.4           # Job scheduling
GitPython==3.1.43             # Git automation
```

### Code Quality (`pyproject.toml`)
```toml
[project]
name = "valhalla"
version = "0.1.0"
requires-python = ">=3.10"

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
select = ["E","F","I","UP","B","SIM","W","Q"]

[tool.mypy]
python_version = "3.10"
warn_unused_configs = true
disallow_untyped_defs = true
```

### Docker Services (`docker-compose.yml` - 11 services)

```yaml
services:
  api:                          # FastAPI app (port 8000)
    build: services/api/Dockerfile
    environment:
      DATABASE_URL: postgresql://valhalla:valhalla@db:5432/valhalla
      HEIMDALL_BUILDER_API_KEY: ${HEIMDALL_BUILDER_API_KEY:-test123}
  
  db:                           # PostgreSQL 16 (port 5432)
    image: postgres:16
    environment:
      POSTGRES_USER: valhalla
      POSTGRES_PASSWORD: valhalla
      POSTGRES_DB: valhalla
  
  heimdall:                     # AI agent container (Python 3.11-slim)
    image: python:3.11-slim
    command: ["sleep", "infinity"]
    volumes: [".:/app"]
    environment:
      GIT_AUTHOR_NAME: "Heimdall Bot"
      DISCORD_WEBHOOK_URL: ${DISCORD_WEBHOOK_URL}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
  
  prometheus:                   # Metrics (port 9090)
    image: prom/prometheus:v2.54.1
    volumes:
      - ./ops/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./ops/prometheus/rules.yml:/etc/prometheus/rules.yml:ro
  
  grafana:                      # Dashboards (port 3000)
    image: grafana/grafana:11.2.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GF_SECURITY_ADMIN_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-piechart-panel,grafana-worldmap-panel
  
  alertmanager:                 # Alert routing (port 9093)
    image: prom/alertmanager:v0.27.0
    volumes:
      - ./ops/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
  
  vector:                       # Log shipping (port 8686)
    image: timberio/vector:0.43.0-debian
    volumes:
      - ./ops/vector/vector.yaml:/etc/vector/vector.yaml:ro
    environment:
      VECTOR_S3_ENABLE: ${VECTOR_S3_ENABLE}
      VECTOR_OS_ENABLE: ${VECTOR_OS_ENABLE}
  
  tempo:                        # Distributed tracing (port 3200)
    image: grafana/tempo:2.5.0
    volumes:
      - ./ops/tempo/tempo.yaml:/etc/tempo.yaml:ro
  
  otel-collector:               # OpenTelemetry (ports 4317, 4318)
    image: otel/opentelemetry-collector:0.101.0
    volumes:
      - ./ops/otel-collector/config.yaml:/etc/otelcol/config.yaml:ro
  
  blackbox:                     # HTTP monitoring (port 9115)
    image: prom/blackbox-exporter:v0.25.0
    volumes:
      - ./ops/blackbox/blackbox.yml:/etc/blackbox/blackbox.yml:ro
  
  ngrok:                        # Tunnel service (port 4040 for UI)
    image: ngrok/ngrok:latest
    command: "http api:8000"
    environment:
      NGROK_AUTHTOKEN: ${NGROK_AUTHTOKEN}
```

---

## 🔑 Key Features & Modules

### Core Features (Always Available)
- ✅ **Health Checks** - `/api/health/live`, system health monitoring
- ✅ **Metrics** - Prometheus-compatible metrics endpoint
- ✅ **Telemetry** - OpenTelemetry traces & spans
- ✅ **Analytics** - Data analysis endpoints
- ✅ **Alerts** - Discord notifications & alert system
- ✅ **Roles** - RBAC system
- ✅ **Admin UI** - Administrative dashboard
- ✅ **UI Dashboard** - User-facing dashboard
- ✅ **Capital** - Capital metrics tracking

### Feature Flags (Conditional Modules)
The application has **70+ feature routers** that are conditionally loaded:

**Available Modules** (based on import success):
- Grants, Buyers, Deals, Match, Contracts
- Intake, Notify, Messaging, Payments
- Negotiations, RBAC, Influence
- Negotiation Strategies, Leads
- Advanced Negotiation, Behavioral Profiling
- Deal Analyzer, Closers, Workflows
- Audit, Freeze, Knowledge, Scheduled Jobs
- Compliance, Orchestrator, FinOps, Arbitrage
- Docs, Policies, Providers, Behavior
- BRRRR, Accounting, Legal
- Black Ice, Queen, King, Pantry, Resort
- Integrity, Tax
- Heimdall Training, Underwriter
- Closer Engine, Contract Engine, Buyer Match

**Pattern**: Each module attempts import with try/except, sets availability flag, continues if import fails (graceful degradation).

---

## 🤖 Heimdall AI System

**Heimdall** is an autonomous AI agent system with several capabilities:

### 1. **Semantic Search Workflow**
- Ingests documentation via `/research/ingest`
- Computes embeddings using external models (OpenAI, Cohere, etc.)
- Stores vectors in database linked to documents
- Enables semantic querying of documentation
- Architecture documented in `HEIMDALL_SEMANTIC_WORKFLOW.md` (509 lines)

### 2. **Auto-Builder System**
- Programmatic code generation via Builder API
- Whitelisted directories for safe editing
- Git-based change tracking
- Dry-run validation before applying changes
- GitHub Actions integration
- Documented in `AUTO_BUILDER_GUIDE.md` (421 lines)

### 3. **Admin Routes** (in `backend/main.py`)
- Auto-PR status & trigger: `/admin/heimdall/api/autopr/status`, `/admin/heimdall/autopr/run`
- Alerts status & testing: `/admin/heimdall/api/alerts/status`, `/admin/heimdall/api/alerts/test`
- Discord notifications via `backend.notify`

### 4. **Research Core**
- Documentation: `RESEARCH_CORE_SETUP.md`
- Embeddings system for RAG (Retrieval Augmented Generation)
- ResearchDoc model with embedding storage

---

## 🗄️ Database & Migrations

### Setup
- **Local Dev**: SQLite (`valhalla.db`) for quick testing
- **Docker**: PostgreSQL container (postgres:16)
- **Production**: Render Postgres (auto-configured via DATABASE_URL)

### Migrations
- **Tool**: Alembic
- **Locations**: 
  - `alembic/` (root level)
  - `services/api/alembic/` (service-specific)
- **Pattern**: Always create migrations for schema changes (no ad-hoc drift)

### SQLAlchemy Models
- **Version**: 2.0 (ORM, async support where applicable)
- **Pattern**: Models in `app/models/`, schemas in `app/schemas/`
- **Pydantic**: v2 with `from_attributes = True` for ORM mode

---

## 🚀 Development Workflow

### Local Development (Windows PowerShell)

```powershell
# 1. Setup virtual environment
cd "c:\dev\valhalla"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r services\api\requirements.txt

# 2. Run dev server (foreground with auto-reload)
.\.venv\Scripts\python.exe -m uvicorn services.api.main:app --reload --port 4000

# 3. Test endpoints
Invoke-RestMethod http://127.0.0.1:4000/api/health | ConvertTo-Json -Depth 5
```

### Docker Development

```powershell
# Start full stack
docker compose up --build

# Services available:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000  
# - Ngrok UI: http://localhost:4040
# - Postgres: localhost:5432
```

### Key Endpoints
- **Health**: `GET /api/health/live` → `{"status":"ok"}`
- **OpenAPI**: `GET /api/v1/openapi.json`
- **Metrics**: Prometheus-compatible metrics endpoint
- **Admin**: Various admin routes under `/admin/`

---

## 📋 Code Standards (from `AI_GUIDE.md`)

### Non-Negotiables
1. **Fix runtime errors before refactors**
2. **Keep public API routes stable** unless explicitly asked to change
3. **Add Alembic migrations** for all DB schema changes
4. **No ad-hoc schema drift**

### Code Style
- **Indentation**: 4 spaces, no tabs
- **Python**: 3.11+, type hints preferred
- **Async**: Use async/await for I/O-bound operations
- **Imports**: Add missing imports, remove dead code
- **Logging**: Use logging framework, not bare `print()`
- **Types**: Prefer `Annotated` for FastAPI dependencies

### Auto-Fixers Configured
- **Black**: Line length 100, target Python 3.10+
- **isort**: Black-compatible profile
- **Ruff**: Select E, F, I, UP, B, SIM, W, Q
- **mypy**: Strict mode, no untyped defs

---

## 🔧 Configuration & Environment

### Key Environment Variables
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/valhalla
HEIMDALL_BUILDER_API_KEY=test123  # or actual key
NGROK_AUTHTOKEN=<your_token>
PYTHONUNBUFFERED=1

# Vector/logging
VECTOR_ENABLED=true
VECTOR_S3_ENABLE=true/false
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>

# OpenSearch
VECTOR_OS_ENABLE=true/false
VECTOR_OS_ENDPOINT=<endpoint>
```

### Settings Location
- `services/api/app/core/settings.py`
- Uses `pydantic-settings` for env var management

---

## 📚 Documentation Files

The project has **extensive documentation** across multiple README files:

### Core Docs
- `README.md` - Main project overview & quickstart
- `AI_GUIDE.md` (159 lines) - Engineering brief for AI agents
- `DEV_WORKFLOW.md` (61 lines) - Daily developer workflow
- `TESTING.md` - Test procedures

### Infrastructure & Operations
- `README.health.md` - Health check system
- `README.metrics.md` - Metrics & monitoring
- `README.telemetry.md` - OpenTelemetry setup
- `README.logging.md` - Logging configuration
- `README.alerts.md` - Alert system
- `README.alerts_auto.md` - Automated alerts
- `README.ci.md` - CI/CD pipeline
- `README.dashboard.md` - Dashboard features
- `README.ui_dashboard.md` - UI dashboard specifics

### Feature-Specific Docs
- `README.analytics.md` - Analytics system
- `README.encryption.md` - Encryption features
- `README.roles.md` - RBAC roles
- `README.research.md` - Research system
- `README.security.md` - Security practices

### Service-Level Docs (in `services/api/`)
- `README.leads.md` - Lead management
- `README.messaging.md` - Messaging system
- `README.negotiations.md` - Negotiation features
- `README.negotiation_strategies.md` - Strategy system
- `README.notifications.md` - Notification system
- `README.payments.md` - Payment processing
- `README.rbac.md` - Role-based access control
- `README.users.md` - User management
- `README.metrics.md` - Service metrics
- Plus many more (pack75_76, pack81_85, etc.)

### Heimdall Docs
- `HEIMDALL_SEMANTIC_WORKFLOW.md` (509 lines) - Semantic search architecture
- `AUTO_BUILDER_GUIDE.md` (421 lines) - Auto-builder system
- `BUILDER_API_EXAMPLES.md` - API usage examples

### Deployment & Operations
- `RENDER_CREDENTIALS.md` - Render.com deployment info
- `CAPITAL_METRICS_DEPLOYMENT.md` - Capital metrics deployment
- `render.yaml` - Render service configuration

---

## 🧪 Testing

### Test Files Present
- `test_builder_api.py` - Builder API tests
- `test_telemetry.py` - Telemetry tests
- `run_health_test.py` - Health check tests
- `test_*.ps1` - PowerShell test scripts for various features

### Test Patterns
```powershell
# Run tests in Docker
docker compose exec api pytest -q app/tests

# Local tests
.\.venv\Scripts\python.exe -m pytest
```

---

## 🔄 CI/CD & Automation

### GitHub Actions
- Auto-builder workflow (`.github/workflows/auto-builder.yml`)
- Auto-PR system (`scripts/ci/auto_pr.py`)
- Status tracking in `dist/docs/auto_pr_status.json`

### Scripts Available
- `fix-research.ps1` - Research system fixes
- `test-research-core.ps1` - Research core testing
- `test-embeddings.ps1` - Embedding system tests
- `wait_for_deploy.ps1` - Deployment waiting
- `wait_and_test_production.ps1` - Production validation
- Various `test_*.ps1` scripts for different features

---

## 🚨 Current Challenges & Context

### Architecture Complexity
- **Multiple backends**: Both `backend/` and `services/api/` exist
- **70+ conditional routers**: Feature flag system means many modules may not be loaded
- **Graceful degradation**: Import failures are caught, making it hard to know what's actually running

### State of Development
- **MVP Focus**: Wholesaling + buyer matching + import/export jobs
- **Feature flags**: Non-blocking modules behind flags (Shield, FunFund, etc.)
- **Migration alignment**: Need to ensure all schema changes have Alembic migrations
- **Type coverage**: Some areas need better type hints

### Common Issues to Watch
1. Indentation/async misuse in workers
2. Missing imports or dead code
3. Type errors (add `Annotated` for deps)
4. Using `print()` instead of proper logging
5. Schema changes without migrations
6. Export jobs need `progress`, `progress_msg`, timestamps, and indexes

---

## 🎯 Next Steps / TODO Areas

Based on the guides, these are typical ongoing tasks:

1. **Runtime Fixes**: Address any blocking runtime errors first
2. **Migration Alignment**: Ensure all DB changes have Alembic migrations
3. **Lint/Format**: Run black, isort, ruff on codebase
4. **Type Safety**: Add type hints, use mypy for validation
5. **Logging**: Replace print statements with proper logging
6. **Tests**: Expand test coverage for critical paths
7. **Documentation**: Keep README files updated with feature changes

---

## 📞 Key Commands Reference

### Start Services
```powershell
# Full Docker stack
docker compose up --build

# API only (local)
.\.venv\Scripts\python.exe -m uvicorn services.api.main:app --reload --port 4000
```

### Database
```powershell
# Connect to Docker Postgres
docker compose exec db psql -U valhalla -d valhalla

# Run migrations
docker compose exec api alembic upgrade head
```

### Testing
```powershell
# Run tests
docker compose exec api pytest -q app/tests

# Test specific endpoint
Invoke-RestMethod http://localhost:8000/api/health/live
```

### Monitoring
- Ngrok UI: http://localhost:4040
- Vector: http://localhost:8686
- Tempo: http://localhost:3200
- Blackbox: http://localhost:9115

---

## 🔐 Security & Credentials

- **API Keys**: Stored in environment variables
- **Secrets**: Never committed to repo
- **Render**: Production credentials in `RENDER_CREDENTIALS.md`
- **Builder API**: Key in `HEIMDALL_BUILDER_API_KEY` env var
- **Encryption**: See `README.encryption.md` for details

---

## 📦 Dependencies

### Python (`requirements.txt`)
```
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
pydantic-settings==2.4.0
sqlalchemy==2.0.35
alembic==1.13.2
psycopg2-binary==2.9.11
httpx==0.27.2
gunicorn==21.2.0
sentry-sdk, boto3, PyYAML, Jinja2
python-slugify, python-multipart, loguru
feedparser, beautifulsoup4, requests
APScheduler, GitPython
```

### Dev Dependencies (`requirements-dev.txt`)
Additional tooling for development

### Frontend (`frontend/package.json`)
Next.js and React dependencies

---

## 🎓 Learning Resources

To understand this project quickly:
1. Read `AI_GUIDE.md` first - engineering principles
2. Then `DEV_WORKFLOW.md` - practical dev setup
3. Review `HEIMDALL_SEMANTIC_WORKFLOW.md` - AI system architecture
4. Check `AUTO_BUILDER_GUIDE.md` - automation capabilities
5. Explore feature-specific READMEs as needed

---

## ✅ Quick Health Check

To verify the system is working:

```powershell
# 1. Start services
docker compose up -d

# 2. Check API health
Invoke-RestMethod http://localhost:8000/api/health/live

# 3. Check admin panel
Invoke-RestMethod http://localhost:8000/admin/heimdall/api/alerts/status

# 4. View logs
docker compose logs -f api
```

Expected healthy output: `{"status":"ok"}` from health endpoint

---

## 📝 Notes for AI Assistants

When helping with this project:
- **Always check** which routers are actually loaded (availability flags in main.py)
- **Database changes** require Alembic migrations
- **Code style**: 4 spaces, type hints, async patterns
- **Testing**: Add tests for new features
- **Documentation**: Update relevant README files
- **Imports**: Watch for conditional imports with try/except
- **FastAPI patterns**: Use Annotated for dependencies
- **Pydantic v2**: Remember `from_attributes = True`
- **SQLAlchemy 2.0**: Async-compatible ORM patterns

---

**End of Handover Document**

Generated from workspace at: `c:\dev\valhalla\`  
For questions or updates, refer to the comprehensive documentation in the project README files.
