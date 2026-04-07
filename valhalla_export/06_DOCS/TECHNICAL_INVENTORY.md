# VALHALLA PROJECT - TECHNICAL INVENTORY & FILE MAPPINGS

**Generated**: March 26, 2026  
**Purpose**: Complete file and module inventory for dev team review

---

## 📊 PROJECT STATISTICS

| Category | Count | Details |
|----------|-------|---------|
| **Python Files** | 83+ | Core application files |
| **Code Lines** | 4,300+ | Total lines of code |
| **API Endpoints** | 42+ | REST API endpoints |
| **Database Models** | 20+ | SQLAlchemy models |
| **Services** | 8+ | Business logic services |
| **Routers** | 11 | API endpoint routers |
| **Database Migrations** | 130+ | Alembic version history |
| **Test Files** | 20+ | Pytest test modules |
| **Documentation Files** | 600+ | Markdown guides |
| **Packs** | 50 | Module implementations |
| **External Integrations** | 6+ | Third-party services |

---

## 🏗️ CORE APPLICATION FILES

### API Entry Points (3 files)
```
app/main.py                           # FastAPI wrapper (thin re-export)
backend/app/main.py                   # Real FastAPI app implementation
services/api/app/main.py              # Service-layer re-export
```

### Configuration Files (12 files)
```
pyproject.toml                        # Project metadata, tool config
requirements.txt                      # Python dependencies
alembic.ini                          # Database migration config
pytest.ini                           # Pytest configuration
.coveragerc                          # Test coverage config
.env.example                         # Dev environment template
.env.example.prod                    # Production template
.env.test                            # Test environment
.env.sandbox                         # Sandbox environment
docker-compose.yml                   # Docker services
Dockerfile                           # Container image definition
Makefile                             # Build automation
```

### Database Layer (20+ files)

**Migration System**:
```
alembic/env.py                       # Migration environment setup
alembic/script.py.mako               # Migration template
alembic/versions/61eede990fb0_baseline_full_system.py  # Base schema
alembic/versions/0068_pack_*.py      # 50 module migrations
alembic/versions/ci*.py              # Classification intelligence
alembic/versions/cl*.py              # Classification learning
```

**Models** (backend/app/models/):
```
base.py                              # Base model class
story.py                             # Story domain model
media.py                             # Media domain model
education.py                         # Education domain model
governance.py                        # Governance domain model
<20+ additional models>              # Domain-specific models
```

**Database Connection**:
```
backend/db.py                        # Connection pool, session factory
```

### Service Layer (15+ files)

**Main Services** (backend/app/services/):
```
story_service.py                     # Story processing
media_service.py                     # Media handling
education_service.py                 # Learning module
governance_service.py                # Governance rules
intake_service.py                    # Intake processing
metrics_service.py                   # Metrics tracking
outcome_service.py                   # Outcome tracking
<additional services>
```

**Specialized Services** (services/):
```
auth_service.py                      # JWT authentication
brain_and_deals.py                   # Deal intelligence
brain_intelligence.py                # AI decision engine
learning_and_scaling.py              # Learning system
sandbox.py                           # Sandbox environment
learning_and_scaling_exports.py      # Learning exports
```

### API Routers (11 files)

**Backend Routers** (backend/app/routers/):
```
story_engine.py                      # Story API endpoints
media_engine.py                      # Media API endpoints
education_engine.py                  # Education API endpoints
governance_decisions.py              # Governance API endpoints
intake.py                            # Intake endpoints
intake_admin.py                      # Intake administration
engine_admin.py                      # Engine administration
metrics.py                           # Metrics endpoints
outcomes.py                          # Outcomes endpoints
runbook_status.py                    # Operational status
example_guarded_endpoints.py         # Example endpoints
```

### Schemas & Validation (15+ files)

**Backend Schemas** (backend/app/schemas/):
```
story.py                             # Story schema definitions
media.py                             # Media schema definitions
education.py                         # Education schemas
governance.py                        # Governance schemas
<additional schemas>
```

### Business Logic & Engines (20+ files)

**Core Engines** (app/core/):
```
data_intake.py                       # Data intake pipeline
engines.py                           # Engine registry
gates.py                             # Access control gates
metrics.py                           # Metrics calculation
outcomes.py                          # Outcome determination
runbook.py                           # Operational procedures
```

**AI Modules** (app/ai/):
```
builder.py                           # AI builder
jobs.py                              # Job scheduling
learn.py                             # Learning module
interlink.py                         # System interconnection
providers.py                         # Provider integrations
```

### Capital Management (8 files)

**Banking System** (capital/banking/):
```
registry.py                          # Capital flow registry
models.py                            # Capital data models
executor.py                          # Payment execution logic
approvals.py                         # Payment approval workflow
caps.py                              # Capital limits
kill_switch.py                       # Emergency shutdown
intake_wizard.py                     # Capital entry workflow
metrics.py                           # Capital metrics
```

### Database CRUD Operations (15+ files)

**CRUD Operations** (backend/app/crud/):
```
crud_story.py                        # Story CRUD
crud_media.py                        # Media CRUD
crud_education.py                    # Education CRUD
crud_governance.py                   # Governance CRUD
<additional CRUD modules>
```

### Security & Middleware (8 files)

**Security** (backend/security/):
```
auth.py                              # Authentication utilities
jwt.py                               # JWT token handling
permissions.py                       # Permission checks
roles.py                             # Role definitions
```

**Middleware** (backend/middleware/):
```
cors.py                              # CORS configuration
request_id.py                        # Request tracking
error_handler.py                     # Error handling
logging.py                           # Request logging
```

### Worker & Task Processing (5 files)

**Background Processing** (backend/workers/):
```
task_queue.py                        # Task queue setup
daily_ops.py                         # Daily operations
webhook_processor.py                 # Webhook handling
scheduled_jobs.py                    # Scheduled job runner
metrics_aggregator.py                # Metrics aggregation
```

### Observability & Monitoring (8 files)

**Observability** (backend/app/observability/):
```
logging.py                           # Structured logging
metrics.py                           # Prometheus metrics
tracing.py                           # Distributed tracing
health.py                            # Health checks
monitoring.py                        # Monitoring utilities
alerts.py                            # Alert configuration
dashboard.py                         # Dashboard metrics
```

---

## 🧪 TEST SUITE (20+ files)

### Test Structure (tests/):
```
conftest.py                          # Pytest configuration
pytest.ini                           # Pytest settings

# Pack Integration Tests (50 tests)
test_pack_0001_*.py
test_pack_0002_*.py
...
test_pack_0050_*.py

# Batch Tests
test_batch_1.py                      # Batch 1 tests
test_batch_2.py                      # Batch 2 tests
test_batch_3.py                      # Batch 3 tests

# Health & Smoke Tests
test_health.py                       # Health endpoint tests
test_smoke.py                        # Smoke tests
test_security.py                     # Security tests

# Component Tests
test_story_engine.py                 # Story engine tests
test_media_engine.py                 # Media engine tests
test_intake.py                       # Intake tests
test_auth.py                         # Auth tests

# Golden Test Data
golden/
  ├── sample_deals.json              # Sample deal data
  ├── sample_contracts.json          # Sample contracts
  ├── payment_scenarios.json         # Payment test data
  └── expected_outputs.json          # Expected results
```

---

## 📚 DOCUMENTATION (600+ files)

### Core Documentation (20+ files)
```
README.md                            # Main readme
PROJECT_STATUS.md                    # Project status
PROJECT_HANDOFF_COMPLETE.md          # This handoff document
COMPLETE_SYSTEM_SUMMARY.md           # System overview
50_MODULES_FINAL_SUMMARY.md          # All 50 modules
VALHALLA_COMPLETE_VISUAL_SUMMARY.md  # Architecture diagrams
```

### Module Documentation (50+ files)
```
MODULES_1_5_COMPLETE.md              # Modules 1-5
MODULES_6_10_COMPLETE.md             # Modules 6-10
MODULES_11_20_COMPLETE.md            # Modules 11-20
MODULES_21_35_COMPLETE.md            # Modules 21-35
MODULES_36_50_COMPLETE.md            # Modules 36-50
```

### Pack Documentation (100+ files)
```
PACK_001_*.md                        # Module pack docs (50x)
PACK_WIRING_*.md                     # Pack wiring docs
PACK_DEPLOYMENT_*.md                 # Pack deployment docs
```

### Deployment & Operations (50+ files)
```
DEPLOYMENT_*.md                      # Deployment guides (multiple)
CANONICAL_DEPLOYMENT.md              # Standard deployment
RAPID_DEPLOYMENT.md                  # Quick deployment
PHASE_1_DEPLOYMENT.md                # Phase 1 deployment
PHASE_2_DEPLOYMENT.md                # Phase 2 deployment
BATCH_1_DEPLOYMENT.md                # Batch 1 deployment
BATCH_2_DEPLOYMENT.md                # Batch 2 deployment
BATCH_3_DEPLOYMENT.md                # Batch 3 deployment
```

### Infrastructure & Governance (30+ files)
```
governance/
  ├── COMPLEXITY_BUDGET.md
  ├── DECISION_FRAMEWORK.md
  ├── ENGINE_KILL_RULES.md
  ├── LOGIC_GUARDRAILS.md
  ├── MONEY_MOVEMENT_POLICY.md
  ├── OPERATOR_PROTECTION.md
  └── (10+ more policy files)
```

### Feature & Integration Documentation (100+ files)
```
README_*.md                          # Feature guides (100+)
API_ENDPOINTS_*.md                   # API documentation
CONTRACT_PIPELINE_*.md               # Contract processing
CSV_INGESTION_*.md                   # Data ingestion
CAPITAL_METRICS_*.md                 # Capital metrics
<many more specialized guides>
```

---

## 🔧 INFRASTRUCTURE & OPS (50+ files)

### Docker & Containers
```
Dockerfile                           # Production image
docker-compose.yml                   # Local development
docker-compose.prod.yml              # Production compose
.dockerignore                        # Docker ignore file
```

### Cloud Deployment
```
render.yaml                          # Render.com deployment
terraform/                           # Infrastructure as Code
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  └── (IaC configuration)
```

### Observability Stack (20+ files)

**Prometheus** (ops/prometheus/):
```
prometheus.yml                       # Scrape config
recording_rules.yml                  # Recording rules
alerting_rules.yml                   # Alerting rules
```

**Grafana** (ops/grafana/):
```
grafana.ini                          # Grafana config
dashboards/
  ├── system_metrics.json
  ├── app_metrics.json
  └── (dashboard definitions)
datasources/
  ├── prometheus.json
  └── (datasource config)
```

**Tempo** (ops/tempo/):
```
tempo.yml                            # Trace config
```

**OpenTelemetry** (ops/otel-collector/):
```
otel-collector-config.yml            # Collector config
```

**Alertmanager** (ops/alertmanager/):
```
alertmanager.yml                     # Alert configuration
```

### Testing & Load Testing
```
ops/k6/
  ├── load_test.js                   # K6 load test script
  ├── stress_test.js                 # Stress test
  └── smoke_test.js                  # Smoke test
```

### Automation Scripts (10+ files)
```
scripts/
  ├── ci/                            # CI/CD scripts
  ├── ingest/                        # Data ingestion
  ├── generate_from_manifest.py      # Code generation
  ├── run_daily_ops.py               # Daily ops runner
  ├── seed.sh                        # Database seeding
  ├── login.sh                       # Auth login
  └── (additional scripts)
```

### Operational Runbooks (15+ files)
```
ops/runbooks/
  ├── deployment_procedure.md
  ├── emergency_procedures.md
  ├── incident_response.md
  ├── monitoring_setup.md
  └── (operational guides)
```

---

## 📦 DEPENDENCY TREE

### Core Framework
```
fastapi==0.115.0
├── pydantic==2.9.2
├── starlette (dependency)
└── (web framework dependencies)

uvicorn==0.30.6
├── click (CLI)
└── (server dependencies)

gunicorn==21.2.0
└── (production server)
```

### Database
```
sqlalchemy==2.0.35
├── alembic==1.13.2
└── psycopg2-binary==2.9.11
```

### Data Validation
```
pydantic==2.9.2
└── pydantic-settings==2.4.0
```

### HTTP & Web
```
httpx==0.27.2
requests==2.32.3
python-multipart==0.0.6
Jinja2==3.1.4
PyYAML==6.0.2
```

### Data Processing
```
beautifulsoup4==4.12.3
feedparser==6.0.11
python-slugify==8.0.4
```

### Cloud & Storage
```
boto3 (AWS SDK)
sentry-sdk (Error tracking)
```

### Utilities
```
loguru==0.7.0
python-json-logger==2.0.7
APScheduler==3.10.4
GitPython==3.1.43
```

### Observability
```
opentelemetry-api==1.21.0
opentelemetry-sdk (extends above)
opentelemetry-exporter-prometheus (Prometheus export)
opentelemetry-exporter-otlp (OTLP export)
```

---

## 🔐 ENVIRONMENT VARIABLES

### Development (.env)
```env
# Core
ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://localhost/valhalla
DB_POOL_SIZE=5
DB_POOL_RECYCLE=3600

# Authentication
JWT_SECRET=dev-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Server
API_TITLE=Valhalla API
API_VERSION=1.0.0
API_DESCRIPTION=Autonomous Income Engine
```

### Production (.env.prod)
```env
# Core
ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://<user>:<pass>@<host>/<db>
DB_POOL_SIZE=20
DB_POOL_RECYCLE=3600

# Authentication
JWT_SECRET=<secure-random-string>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AWS S3
S3_BUCKET=valhalla-prod
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=<aws-access-key>
S3_SECRET_ACCESS_KEY=<aws-secret>

# Stripe
STRIPE_API_KEY=<stripe-key>
STRIPE_WEBHOOK_SECRET=<webhook-secret>

# DocuSign
DOCUSIGN_POWERFORM_URL=<docusign-url>
DOCUSIGN_INTEGRATOR_KEY=<integrator-key>

# QuickBooks
QB_CLIENT_ID=<qb-client-id>
QB_CLIENT_SECRET=<qb-secret>
QB_REALM_ID=<qb-realm>

# Plaid
PLAID_CLIENT_ID=<plaid-id>
PLAID_SECRET=<plaid-secret>

# Monitoring
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_ENABLED=true
```

---

## 🚀 API ENDPOINTS OVERVIEW

### System Endpoints (5)
```
GET    /                           # API root
GET    /docs                       # Swagger UI
GET    /redoc                      # ReDoc documentation
GET    /openapi.json               # OpenAPI schema
GET    /system/health              # Health check
```

### Story Engine (6)
```
GET    /stories                    # List stories
POST   /stories                    # Create story
GET    /stories/{id}               # Get story
PUT    /stories/{id}               # Update story
DELETE /stories/{id}               # Delete story
POST   /stories/{id}/process       # Process story
```

### Media Engine (6)
```
GET    /media                      # List media
POST   /media                      # Upload media
GET    /media/{id}                 # Get media
DELETE /media/{id}                 # Delete media
POST   /media/{id}/process         # Process media
GET    /media/{id}/metadata        # Get metadata
```

### Education Engine (5)
```
GET    /education                  # List courses
POST   /education                  # Create course
GET    /education/{id}             # Get course
PUT    /education/{id}             # Update course
DELETE /education/{id}             # Delete course
```

### Governance Decisions (4)
```
GET    /governance/rules           # List rules
POST   /governance/decisions       # Make decision
GET    /governance/{id}            # Get decision
PUT    /governance/{id}            # Update decision
```

### Intake (5)
```
POST   /intake                     # Submit intake item
GET    /intake                     # Get intake items
GET    /intake/{id}                # Get intake detail
PUT    /intake/{id}                # Update intake
DELETE /intake/{id}                # Delete intake
```

### Admin Endpoints (5)
```
GET    /admin/status               # System status
POST   /admin/reload               # Reload configuration
GET    /admin/metrics              # System metrics
POST   /admin/shutdown             # Graceful shutdown
POST   /admin/kill-switch          # Emergency kill switch
```

### Metrics (3)
```
GET    /metrics/system             # System metrics
GET    /metrics/performance        # Performance metrics
GET    /metrics/export             # Export metrics (Prometheus)
```

### Other (3+)
```
GET    /outcomes                   # Get outcomes
GET    /runbook/status             # Runbook status
... (additional endpoints)
```

**Total**: 42+ endpoints

---

## 📊 DATABASE SCHEMA STRUCTURE

### Core Tables
```
stories          # Story entities
media            # Media files
education        # Education modules
governance       # Governance rules
deals            # Real estate deals
contracts        # Contracts
payments         # Payment records
outcomes         # System outcomes
metrics          # Performance metrics
<15+ additional tables>
```

### Indexes
```
stories.created_at (descending)
media.s3_key (unique)
deals.status_code (ascending)
payments.stripe_id (unique)
contracts.docusign_id (unique)
<10+ additional indexes>
```

### Foreign Keys
```
stories → users
media → stories
contracts → deals
payments → contracts
outcomes → system_actions
<additional relationships>
```

---

## 🔄 MODULE BREAKDOWN (50 Modules)

### Phase 1: Core (1-20)
- Module 1-2: Authorization & Security
- Module 3-12: Contract Pipeline (PDF, DocuSign, S3)
- Module 13-14: Deal Scoring & Analysis
- Module 15-20: Offer Generation & Communication

### Phase 2: Extended (21-35)
- Module 21: Stripe Payment Processing
- Module 22: QuickBooks Accounting
- Module 23: System Activation
- Module 24-35: Advanced Features & Admin

### Phase 3: Operations (36-50)
- Module 36-37: Webhooks & Notifications
- Module 38: External Integrations
- Module 39-40: Safety & Kill Switches
- Module 41-50: Monitoring & Operations

---

## ✅ QUALITY ASSURANCE

### Code Quality Tools
- **Black** (Line length: 100)
- **isort** (Import sorting)
- **ruff** (Fast linting)
- **mypy** (Type checking)
- **pytest** (Testing)
- **coverage** (Code coverage)

### Target Metrics
- Code Coverage: 80%+
- Type Completion: 95%+
- Lint Issues: 0
- Format: Consistent

---

## 📝 FILE SUMMARY

| Category | Count |
|----------|-------|
| Python Files | 83+ |
| Test Files | 20+ |
| Documentation | 600+ |
| Configuration | 15+ |
| Infrastructure | 50+ |
| **Total Files** | **768+** |

---

**Last Updated**: March 26, 2026  
**Status**: Complete Inventory  
**Purpose**: Technical reference for dev team
