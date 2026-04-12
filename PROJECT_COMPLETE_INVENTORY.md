# VALHALLA PROJECT - COMPLETE TECHNICAL INVENTORY

## Project Overview

**Project Name:** Valhalla  
**Type:** FastAPI-based Backend API Platform  
**Version:** 1.0.0  
**Status:** Production Ready  
**Language:** Python 3.8+  
**Deployment:** FastAPI + Uvicorn (with Gunicorn for production)

---

## Executive Summary

Valhalla is a comprehensive, multi-featured API platform designed for complex business operations including deal management, lead acquisition, governance orchestration, contracts lifecycle, payments, and advanced analytics. The system features:

- **150+ API Routers** with hundreds of endpoints
- **Advanced Governance Systems** including decision management, policy enforcement, and orchestration
- **Heimdall Agent Integration** for intelligent workload distribution and task execution
- **Multi-tenant Support** with RBAC (Role-Based Access Control)
- **Complex Business Logic** for real estate deals, lead management, contract workflows
- **Audit & Compliance** systems with complete audit trails
- **Analytics & Reporting** with comprehensive metrics and dashboards
- **Scheduled Jobs & Workers** for background processing
- **Database ORM** with Alembic migrations and SQLAlchemy

---

## Technology Stack

### Core Dependencies

```
FastAPI 0.115.0              # Web framework
Uvicorn 0.30.6               # ASGI server
Gunicorn 21.2.0              # Application server
Pydantic 2.9.2               # Data validation
SQLAlchemy 2.0.35            # ORM
Alembic 1.13.2               # Database migrations
psycopg2-binary 2.9.11       # PostgreSQL adapter
```

### Supporting Libraries

```
Sentry SDK                   # Error tracking
Boto3                        # AWS S3 integration
httpx 0.27.2                 # HTTP client
PyYAML 6.0.2                 # Config files
Jinja2 3.1.4                 # Templating
python-slugify 8.0.4         # URL slugs
python-multipart 0.0.6       # File uploads
loguru 0.7.0                 # Advanced logging
python-json-logger 2.0.7     # JSON logging
```

### Observability

```
opentelemetry-api 1.21.0     # Distributed tracing
APScheduler 3.10.4           # Job scheduling
```

### Optional/Data Processing

```
feedparser 6.0.11            # RSS parsing
beautifulsoup4 4.12.3        # Web scraping
requests 2.32.3              # HTTP library
GitPython 3.1.43             # Git operations
```

---

## Architecture Overview

### Directory Structure

```
d:\dev\
├── app/                          # Thin entrypoint that re-exports main app
├── services/
│   └── api/
│       └── app/                   # MAIN APPLICATION ROOT
│           ├── routers/           # 150+ API route modules (see below)
│           ├── models/            # SQLAlchemy ORM models
│           ├── schemas/           # Pydantic request/response schemas
│           ├── services/          # Business logic services
│           ├── core/              # Core utilities
│           │   ├── db.py          # Database connection
│           │   └── config.py      # Configuration
│           ├── middleware/        # Express middleware
│           ├── auth/              # Authentication services
│           ├── observability/     # Logging & monitoring
│           ├── main.py            # FastAPI app initialization
│           └── [40+ feature modules]
├── alembic/                       # Database migration scripts
├── tests/                         # Test suite
├── docs/                          # API documentation
├── configs/                       # Configuration files
├── scripts/                       # Utility scripts
└── requirements.txt               # Python dependencies
```

### Application Boot Flow

1. **Entry Point**: `app/main.py` (thin wrapper)
   - Re-exports `services.api.app.main:app`

2. **Main App**: `services/api/app/main.py`
   - Creates FastAPI app instance
   - Registers system boot router (admin endpoints)
   - Registers Heimdall Jarvis router
   - Auto-loads all routers from `app/routers/`
   - Initializes lifespan (async startup/shutdown)
   - Sets up health check endpoints

3. **Router Auto-Loading**
   - All modules in `app/routers/` with a `router` variable are automatically included
   - Skip system_boot (loaded first due to priority)
   - Order: System Boot → Jarvis → Auto-loaded routers

---

## Core Features & Modules

### 1. **System & Admin** (22 routers)

| Module | Purpose |
|--------|---------|
| `admin.py` | Admin panel utilities |
| `admin_bootstrap.py` | System initialization & setup |
| `admin_build.py` | Build management |
| `admin_dashboard.py` | Admin dashboard endpoints |
| `admin_go_live.py` | Go-live coordination |
| `admin_healthcheck.py` | Health monitoring |
| `admin_heimdall.py` | Heimdall agent administration |
| `admin_logs.py` | Log management |
| `admin_ops.py` | Operations management |
| `admin_privacy.py` | Privacy & data protection |
| `admin_secscan.py` | Security scanning |
| `admin_system_summary.py` | System status summary |
| `admin_todo.py` | Task management |
| `system_boot.py` | Core system bootstrap |
| `system_config.py` | Configuration management |
| `system_health.py` | Health status |
| `system_log.py` | System logging |
| `system_selftest.py` | Self-diagnostics |
| `system_status.py` | Overall system status |
| `health.py` | Health check endpoints |
| `deployment_profile.py` | Deployment profiles |
| `deploy_check.py` | Deployment verification |

**Key Endpoints:**
```
GET  /health                  - Quick health check
GET  /healthz                 - K8s health with queue info
GET  /readyz                  - K8s readiness check
GET  /admin/status            - Admin dashboard
GET  /admin/system-summary    - System overview
POST /admin/go-live           - Enable production mode
POST /admin/bootstrap         - Initialize system
```

---

### 2. **Deal Management** (10 routers)

| Module | Purpose |
|--------|---------|
| `deals.py` | Core deal CRUD operations |
| `deal_analyzer.py` | Deal analysis & metrics |
| `deal_finalization.py` | Closing procedures |
| `deal_lifecycle.py` | Deal workflow states |
| `deal_workflow_status.py` | Workflow tracking |
| `wholesale_deals.py` | Wholesale deal management |
| `wholesale_engine.py` | Wholesale deal calculations |
| `flow_lead_to_deal.py` | Lead → Deal conversion pipeline |
| `opportunity.py` | Opportunity tracking |
| `opportunity_tracker.py` | Opportunity analytics |

**Key Endpoints:**
```
POST   /deals                 - Create new deal
GET    /deals                 - List all deals
GET    /deals/{deal_id}       - Get deal details
PUT    /deals/{deal_id}       - Update deal
DELETE /deals/{deal_id}       - Delete deal
GET    /deals/{deal_id}/analysis
POST   /deals/{deal_id}/finalize
GET    /wholesale/deals       - Wholesale deals
POST   /deals/convert         - Lead to deal conversion
```

---

### 3. **Lead Management** (6 routers)

| Module | Purpose |
|--------|---------|
| `leads.py` | Core lead CRUD & intake |
| `leads_status.py` | Lead status tracking |
| `lead_engine.py` | Lead scoring & qualification |
| `registration_navigator.py` | Registration workflow |
| `intake.py` | Lead intake process |
| `intake_admin.py` | Intake administration |

**Key Endpoints:**
```
POST   /leads                 - Create lead
GET    /leads                 - List leads
GET    /leads/{lead_id}       - Get lead
PUT    /leads/{lead_id}/status - Update status
DELETE /leads/{lead_id}       - Delete lead
POST   /leads/intake          - Intake process
GET    /leads/{lead_id}/score - Lead scoring
```

---

### 4. **User & Authentication** (3 routers)

| Module | Purpose |
|--------|---------|
| `users.py` | User management |
| `user_summary.py` | User profile summary |
| `auth/` | (Service layer) Authentication logic |

**Key Endpoints:**
```
POST   /users                 - Create user
GET    /users                 - List users
GET    /users/{user_id}       - Get user
PUT    /users/{user_id}       - Update user
DELETE /users/{user_id}       - Delete user
GET    /users/{user_id}/summary
```

---

### 5. **Governance & Decision Management** (10 routers)

| Module | Purpose |
|--------|---------|
| `governance_orchestrator.py` | Central governance hub |
| `governance_king.py` | King pattern implementation |
| `governance_queen.py` | Queen pattern implementation |
| `governance_loki.py` | Loki strategic governance |
| `governance_odin.py` | Odin decision authority |
| `governance_tyr.py` | Tyr enforcement |
| `governance_policy.py` | Policy management |
| `governance_decisions.py` | Decision tracking |
| `decision_governance.py` | Governance rules |
| `decision_recommendation.py` | Recommendation engine |
| `decision_outcome.py` | Outcome tracking |

**Key Endpoints:**
```
GET    /governance/status     - Governance status
POST   /governance/decide     - Make decision
GET    /governance/policies   - List policies
POST   /governance/policies   - Create policy
GET    /governance/decisions  - List decisions
POST   /governance/outcomes   - Track outcome
```

---

### 6. **Contract Management** (8 routers)

| Module | Purpose |
|--------|---------|
| `contracts.py` | Contract CRUD |
| `contracts_lifecycle.py` | Contract workflow |
| `contracts_pipeline.py` | Contract pipeline |
| `contracts_webhooks.py` | Contract events |
| `contract_engine.py` | Contract automation |
| `document_routing.py` | Document flow |
| `contracts_upload.py` | Document upload |
| `agreements.py` / `agreements_upload.py` | Agreement management |

**Key Endpoints:**
```
POST   /contracts             - Create contract
GET    /contracts             - List contracts
GET    /contracts/{id}        - Get contract
PUT    /contracts/{id}        - Update contract
POST   /contracts/{id}/execute
GET    /contracts/pipeline    - Pipeline status
POST   /contracts/webhooks    - Event registration
```

---

### 7. **Financial Operations** (15 routers)

| Module | Purpose |
|--------|---------|
| `accounting.py` | General accounting |
| `banking_structure_planner.py` | Bank account planning |
| `capital.py` | Capital management |
| `finance.py` | Financial calculations |
| `finops.py` | Financial operations |
| `payments.py` | Payment processing |
| `income_routing.py` | Income distribution |
| `tax_tracker.py` | Tax tracking |
| `tax_bridge.py` | Tax system integration |
| `credit_card_spending.py` | Credit card tracking |
| `buyer_liquidity.py` | Buyer liquidity analysis |
| `grants.py` | Grant management |
| `grant_eligibility.py` | Grant qualification |
| `flow_profit_allocation.py` | Profit distribution |
| `flow_tax_snapshot.py` | Tax reports |

**Key Endpoints:**
```
POST   /accounting/entry      - Record transaction
GET    /accounting/ledger     - View ledger
POST   /payments/process      - Process payment
GET    /finance/summary       - Financial summary
GET    /tax/snapshot          - Tax report
POST   /capital/allocate      - Capital allocation
```

---

### 8. **Analytics & Reporting** (10 routers)

| Module | Purpose |
|--------|---------|
| `analytics.py` | Analytics core |
| `analytics_engine.py` | Analytics calculations |
| `metrics.py` | Metrics tracking |
| `reports.py` | Report generation |
| `portfolio_dashboard.py` | Portfolio view |
| `personal_dashboard.py` | Personal dashboard |
| `operational_dashboard.py` | Ops dashboard |
| `empire_dashboard.py` | Executive dashboard |
| `security_dashboard.py` | Security monitoring |
| `ui_dashboard.py` | UI dashboard backend |

**Key Endpoints:**
```
GET    /analytics/summary     - Analytics overview
GET    /metrics               - Metrics data
POST   /reports/generate      - Generate report
GET    /dashboards/portfolio  - Portfolio dashboard
GET    /dashboards/ops        - Operations dashboard
```

---

### 9. **Notifications & Communications** (7 routers)

| Module | Purpose |
|--------|---------|
| `notifications.py` | Notification core |
| `notification_bridge.py` | 3rd party integration |
| `notification_channel.py` | Channels (Email, SMS, etc) |
| `notification_orchestrator.py` | Notification workflow |
| `messaging.py` | Messaging service |
| `notify.py` | Notify operations |
| `notify_test.py` | Notification testing |

**Key Endpoints:**
```
GET    /notifications         - List notifications
POST   /notifications         - Send notification
GET    /notifications/{id}    - Get notification
POST   /messages/send         - Send message
```

---

### 10. **Compliance & Security** (12 routers)

| Module | Purpose |
|--------|---------|
| `audit.py` | Audit logging |
| `compliance.py` | Compliance rules |
| `security.py` | Security operations |
| `security_actions.py` | Security actions |
| `security_policy.py` | Security policies |
| `security_dashboard.py` | Security monitoring |
| `integrity.py` | Data integrity |
| `integrity_monitor.py` | Integrity checking |
| `encryption.py` | Encryption operations |
| `data_retention.py` | Retention policies |
| `event_log.py` | Event logging |
| `internal_auditor.py` | Internal audit |

**Key Endpoints:**
```
GET    /audit/events          - Audit trail
POST   /audit/events          - Log event
GET    /compliance/status     - Compliance status
POST   /security/scan         - Security scan
GET    /security/policies     - Policy list
```

---

### 11. **AI & Decision Engines** (15+ routers)

| Module | Purpose |
|--------|---------|
| `heimdall.py` | Heimdall AI agent |
| `heimdall_build_gate.py` | Build gates |
| `heimdall_governance.py` | Governance decisions |
| `heimdall_training.py` | AI training |
| `heimdall_workload.py` | Workload management |
| `explanation_engine.py` | Explain decisions |
| `scenario_simulator.py` | Scenario testing |
| `strategic_mode.py` | Strategic execution |
| `narrative.py` | Narrative generation |
| `story_engine.py` | Story creation |
| `story_mode.py` | Story mode operations |
| `recommendation` patterns | Multiple recommendation engines |
| `research.py` | Research operations |
| `research_semantic.py` | Semantic research |
| `insight.py` | Insight generation |

**Key Endpoints:**
```
POST   /heimdall/task         - Submit task
GET    /heimdall/status       - Check status
GET    /heimdall/results      - Get results
POST   /heimdall/train        - Train model
POST   /ai/scenario           - Run scenario
GET    /insights              - Get insights
```

---

### 12. **Business Processes** (20+ routers)

#### Deal Workflows
- `arbitrage.py` - Arbitrage evaluation
- `brrrr.py` / `brrrr_planner.py` - BRRRR analysis
- `closers.py` / `closer_engine.py` - Closer management
- `closing_playbook.py` - Closing procedures

#### Buyer & Investor Operations
- `buyers.py` / `buyer_match.py` - Buyer management & matching
- `investor_module.py` - Investor tracking
- `relationships.py` - Relationship management
- `match.py` - Deal/buyer matching

#### Advanced Negotiations
- `advanced_negotiation_techniques.py` - Negotiation strategies
- `negotiations.py` - Negotiation tracking
- `negotiation_strategies.py` - Strategy management
- `neg_enhance.py` - Negotiation enhancement
- `offer_strategy.py` - Offer management

#### Professional Services
- `specialists.py` - Specialist directory
- `specialist_feedback.py` - Feedback management
- `pro_alignment_engine.py` - Alignment tracking
- `pro_behavioral_extract.py` - Behavior analysis
- `pro_handoff.py` - Handoff procedures
- `pro_scorecard.py` - Professional scoring

**Key Endpoints:**
```
POST   /arbitrage/analyze     - Arbitrage analysis
POST   /brrrr/calculate       - BRRRR calculation
GET    /buyers                - List buyers
POST   /match/find            - Find matches
GET    /negotiations          - List negotiations
POST   /specialists/assign    - Assign specialist
```

---

### 13. **Scheduling & Automation** (6 routers)

| Module | Purpose |
|--------|---------|
| `scheduled_jobs.py` | Job scheduling |
| `job.py` | Job management |
| `jobs.py` | Job operations |
| `cron/` | Cron job handlers |
| `daily_rhythm.py` | Daily tasks |
| `flow_notifications.py` | Notification automation |

**Key Endpoints:**
```
POST   /jobs/schedule         - Schedule job
GET    /jobs                  - List jobs
GET    /jobs/{job_id}         - Job status
DELETE /jobs/{job_id}         - Cancel job
```

---

### 14. **Data & Knowledge** (10+ routers)

| Module | Purpose |
|--------|---------|
| `knowledge.py` | Knowledge base |
| `docs.py` | Documentation |
| `data_lineage.py` | Data tracking |
| `legal.py` / `lawyer_feed.py` | Legal documents |
| `education_engine.py` | Learning content |
| `media_engine.py` | Media management |
| `playbooks.py` | Operational playbooks |
| `pantry.py` | Resource library |
| `research.py` / `research_semantic.py` | Research tools |

**Key Endpoints:**
```
GET    /knowledge             - Browse knowledge
POST   /knowledge/add         - Add KB article
GET    /docs                  - Documentation
GET    /playbooks             - Playbook library
POST   /research/query        - Research query
```

---

### 15. **Monitoring & Logging** (8 routers)

| Module | Purpose |
|--------|---------|
| `telemetry.py` | Telemetry collection |
| `telemetry_event.py` | Event telemetry |
| `logging.py` | Log management |
| `system_log.py` | System logs |
| `health.py` | Health endpoints |
| `metrics.py` | Metrics tracking |
| `maintenance.py` | System maintenance |
| `trajectory.py` | Performance tracking |

**Key Endpoints:**
```
GET    /telemetry/metrics     - Telemetry data
POST   /telemetry/event       - Log event
GET    /logs                  - View logs
GET    /maintenance/status    - Maintenance info
```

---

## API Endpoint Summary

### Total API Routes: 150+ Router Modules

### Endpoint Categories

```
✓ Health & Status Endpoints        (3 endpoints)
✓ Admin & System                   (25+ endpoints)
✓ Deal Management                  (20+ endpoints)
✓ Lead Management                  (15+ endpoints)
✓ User Management                  (10+ endpoints)
✓ Governance                       (20+ endpoints)
✓ Contracts                        (20+ endpoints)
✓ Financial Operations             (30+ endpoints)
✓ Analytics & Reporting            (25+ endpoints)
✓ Notifications                    (15+ endpoints)
✓ Security & Compliance            (25+ endpoints)
✓ AI & Decision Engines            (30+ endpoints)
✓ Business Processes               (50+ endpoints)
✓ Scheduling & Automation          (15+ endpoints)
✓ Knowledge & Data                 (20+ endpoints)
✓ Monitoring & Logging             (20+ endpoints)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL ESTIMATED ENDPOINTS: 350+
```

---

## Database Models

### Core Models (30+ ORM Models)

**Professional & Roles**
- `Professional` - Professional information
- `Scorecard` - Professional scoring
- `InteractionLog` - Interaction tracking
- `Retainer` - Retainer agreements

**Contracts & Documents**
- `ContractTemplate` - Contract templates
- `ContractRecord` - Contract instances
- `DocumentRoute` - Document workflow
- `AuditEvent` - Audit trail

**Deal & Lead Models**
- `LeadSource` - Lead origin tracking
- `RawLead` - Unprocessed leads
- `NormalizedLead` - Processed leads
- (Deal models in core services)

**Governance & Decisions**
- `GovernanceDecision` - Decision records
- `StrategicDecision` - Strategic choices
- `DecisionOutcome` - Outcome tracking
- `EngineStateRow` - Engine state tracking

**Rules & Triggers**
- `TuningRule` - Tuning parameters
- `TriggerRule` - Trigger definitions
- `TriggerEvent` - Triggered events
- `WorkflowGuardrail` - Guardrails

**Strategic & Narrative**
- `StrategicMode` - Strategic execution
- `StrategicEvent` - Strategy events
- `Trajectory` - Progress tracking
- `NarrativeChapter` - Story chapters
- `NarrativeEvent` - Story events
- `ActiveChapter` - Current narrative

**Configuration & Providers**
- `ModelProvider` - AI model registry
- `TuningRule` - Rule tuning
- `ProfessionalTaskLink` - Task assignments

**Approval & Sandbox**
- `PendingAction` - Pending approvals
- `PendingActionStatus` - Approval status
- `SandboxEvent` - Sandbox events
- `HumanLabel` - Manual labels

---

## Database Configuration

### Connection
```python
# Environment variable required:
DATABASE_URL=postgresql://user:pass@host:5432/valhalla

# Or falls back to local SQLite:
sqlite:///./valhalla.db
```

### Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Recent migrationheads fixed in:
ALEMBIC_MULTIPLE_HEADS_FIX.md
ALEMBIC_FIX_FINAL.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (recommended) or SQLite
- pip/virtualenv

### Local Development Setup

```bash
# 1. Navigate to project
cd d:\dev

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -U pip
pip install -r requirements.txt

# 5. Set up environment
cp .env.example .env
# Edit .env as needed

# 6. Run database migrations
alembic upgrade head

# 7. Start development server
uvicorn app.main:app --reload --port 4000
```

### Using VS Code Tasks

```bash
# Install deps
Task: "Install deps"

# Run dev server (port 4000)
Task: "Run (dev)"

# Format code
Task: "Format"

# Lint
Task: "Lint"

# Type check
Task: "Type check"

# Run tests
Task: "Test"
```

---

## Environment Configuration

### Key Configuration Files
```
.env                 - Local dev environment
.env.example         - Template for .env
.env.example.prod    - Production template
.env.sandbox         - Sandbox testing
.env.test            - Test environment
alembic.ini          - Database migration config
pyproject.toml       - Project metadata
pytest.ini           - Test configuration
mypy.ini             - Type checking config
.pre-commit-config.yaml - Pre-commit hooks
```

### Critical Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...  # Required for production
SQLALCHEMY_ECHO=false          # SQL query logging

# AWS/S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=...

# Sentry (Error Tracking)
SENTRY_DSN=...

# Heimdall/Agent
HEIMDALL_CONFIG_PATH=heimdall/agent.config.json
HEIMDALL_QUEUE_DIR=heimdall/queue

# Security
SECRET_KEY=...                 # JWT secret
ALLOWED_ORIGINS=*              # CORS origins

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_PORT=4000
DEBUG=false
```

---

## Running the Application

### Development Mode
```bash
# Fast reload on code changes, port 4000
uvicorn app.main:app --reload --port 4000
```

### Production Mode

#### Using Gunicorn (Recommended)
```bash
# 4 worker processes, port 8000
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

#### Using Docker
```bash
# Build image
docker build -t valhalla:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  valhalla:latest
```

#### Using Docker Compose
```bash
# Production
docker-compose -f docker-compose.yml up -d

# Cron jobs
docker-compose -f Dockerfile.cron up -d
```

### Health Checks

Once running, test with:
```bash
# Quick health
curl http://localhost:4000/health

# K8s health with queue info
curl http://localhost:4000/healthz

# K8s readiness
curl http://localhost:4000/readyz

# Full API docs
curl http://localhost:4000/docs
```

---

## Testing

### Test Suite Structure
```
tests/
├── test_pack_*.py          - Feature pack tests
├── test_endpoints.py       - Endpoint tests
├── test_integration.py     - Integration tests
├── test_migrations.py      - Migration tests
└── conftest.py             - Test configuration
```

### Running Tests

```bash
# All tests
pytest -q

# Specific test file
pytest tests/test_pack_1_3.py

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_endpoints.py::test_create_deal
```

---

## Code Quality

### Linting
```bash
# Ruff (fast Python linter)
ruff check .

# Fix issues
ruff check . --fix
```

### Formatting
```bash
# Black (code formatter)
black .

# isort (import sorting)
isort .

# Combined
Task: "Format"
```

### Type Checking
```bash
# MyPy
mypy .

# Task
Task: "Type check"
```

### Pre-commit Hooks
```bash
# Install
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Project Structure Deep Dive

### Key Directories

#### `/services/api/app/routers/` (150+ modules)
All API endpoints organized by feature domain. Each router:
- Exports a `router` variable (FastAPI router)
- Defines endpoints with proper documentation
- Uses dependency injection for services
- Includes request/response schemas

**Example Router Pattern:**
```python
from fastapi import APIRouter, Depends
from app.schemas.deal import DealCreate, DealOut
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])

@router.post("", response_model=DealOut)
async def create_deal(data: DealCreate, service: DealService = Depends()):
    return await service.create(data)
```

#### `/services/api/app/models/`
SQLAlchemy ORM models - database table definitions with relationships

#### `/services/api/app/schemas/`
Pydantic v2 request/response validation schemas

#### `/services/api/app/services/`
Business logic layer - handles calculations, workflows, integrations

#### `/services/api/app/core/`
- `db.py` - Database engine and session management
- `config.py` - Configuration loading
- Security utilities
- Dependency injection

#### `/services/api/app/auth/`
Authentication and authorization services

#### `/services/api/app/middleware/`
Express middleware for:
- Request/response logging
- Error handling
- Request validation
- CORS

#### `/services/api/app/observability/`
Logging, tracing, and monitoring:
- Sentry integration
- OpenTelemetry tracing
- Structured logging
- Metrics collection

#### `/alembic/`
Database migration scripts using Alembic
```
alembic/
├── versions/              # Migration files
├── env.py                 # Migration environment config
├── script.py.template     # Migration template
└── alembic.ini           # Alembic configuration
```

#### `/tests/`
Test suite with pytest

#### `/docs/`
Generated API documentation

---

## Core Services Architecture

### Service Layer Pattern

Most features follow this pattern:

```
routers/
├── feature.py              # HTTP endpoints
└── schema.py               # Request/response models

services/
└── feature_service.py      # Business logic

models/
└── feature_model.py        # Database models

core/
└── feature_utils.py        # Utilities
```

### Dependency Injection

Uses FastAPI's `Depends()` for:
- Service instances
- Database sessions
- Authentication/authorization
- Configuration

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify and return user
    pass

@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    # User automatically injected
    pass
```

---

## Advanced Features

### 1. **Heimdall AI Agent System**
- Task submission and tracking
- Intelligent workload distribution
- Agent orchestration
- YAML-based configuration
- Queue management (pending/working/done/error states)

**Location:** `app/heimdall/` + `routers/heimdall.py`

### 2. **Governance Engine**
- Policy-based decision making
- Multi-level approval workflows
- Role-based access control
- Audit trails for all decisions

**Location:** `app/governance/` + multiple governance routers

### 3. **Deal Pipeline**
- Multi-stage deal workflow
- Automatic stage transitions
- Compliance checks
- Profit/loss calculations

**Location:** Across deals, contracts, payments routers

### 4. **Lead Score Management**
- Automated lead scoring
- Qualification rules
- Triage and routing
- Conversion tracking

**Location:** `app/leads/` + routers

### 5. **Contract Lifecycle**
- Template management
- Execution workflow
- Document routing
- Electronic signatures

**Location:** `app/contracts/` + routers

### 6. **Financial Operations**
- Multi-currency support
- Tax tracking
- Payment processing
- Profit allocation

**Location:** Multiple finance routers

### 7. **Analytics Engine**
- Real-time metrics
- Custom report generation
- Dashboard data
- KPI tracking

**Location:** analytics & reporting routers

---

## Deployment

### Local Development
```bash
uvicorn app.main:app --reload --port 4000
```

### Staging
```bash
gunicorn -w 2 -b 0.0.0.0:8000 app.main:app
```

### Production
```bash
# Using Render (recommended)
gunicorn -w 4 -b 0.0.0.0:$PORT app.main:app

# Using AWS/Docker
docker run -e DATABASE_URL=$DB_URL myapp:latest
```

### Deployment Files
- `Dockerfile` - Container image
- `docker-compose.yml` - Local development
- `Dockerfile.cron` - Cron job container
- `render.yaml` - Render deployment config
- `entrypoint.sh` - Container startup script

---

## Monitoring & Debugging

### Health Endpoints
```
GET /health              - Quick check (always responds)
GET /healthz             - K8s health with queue stats
GET /readyz              - K8s readiness with heartbeat
```

### Logging
- Structured JSON logging
- Request/response logging
- Application logs in `/logs/`
- Sentry integration for errors

### Diagnostics
```bash
# System diagnostics
GET /admin/system-summary

# Route inspection
python tmp_print_routes.py

# Live workflow testing
python verify_live_workflow.py
```

---

## Key Files for Dev Team

### Configuration
- `.env.example` - Environment setup
- `alembic.ini` - Database config
- `pyproject.toml` - Project metadata
- `pytest.ini` - Test config
- `mypy.ini` - Type checking config

### Documentation
- `README.md` - Main readme
- `docs/` - API documentation
- Multiple deployment guides
- Feature pack documentation

### Testing
- `conftest.py` - pytest configuration
- `tests/test_*.py` - Test suites
- `pytest.ini` - Test settings

### Development
- `requirements.txt` - Python dependencies
- `Makefile` - Common commands
- `.pre-commit-config.yaml` - Code quality hooks

---

## Development Workflow

### Typical Dev Cycle

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Develop with auto-reload**
   ```bash
   uvicorn app.main:app --reload --port 4000
   ```

3. **Format & lint**
   ```bash
   Task: Format
   Task: Lint
   Task: Type check
   ```

4. **Write tests**
   ```bash
   pytest tests/test_new_feature.py
   ```

5. **Run full test suite**
   ```bash
   Task: Test
   ```

6. **Commit & push**
   ```bash
   git add .
   git commit -m "feat: new feature description"
   git push origin feature/new-feature
   ```

7. **Create PR for review**

---

## Common Tasks

### Adding a New Endpoint

1. Create schema in `schemas/feature.py`
2. Create router in `routers/feature.py`
3. Create service in `services/feature_service.py`
4. Add model in `models/feature_model.py`
5. Add migration if schema changes: `alembic revision --autogenerate`
6. Test: `pytest tests/test_feature.py`

### Adding Database Model

1. Create model file in `models/feature.py`
2. Import in `models/__init__.py`
3. Generate migration: `alembic revision --autogenerate -m "add feature table"`
4. Review and apply: `alembic upgrade head`
5. Create ORM model tests

### Fixing Issues

1. Check logs: `GET /logs` or `/var/logs/app.log`
2. Review audit trail: `GET /audit/events`
3. Check health: `GET /readyz`
4. Run diagnostics: `GET /admin/system-summary`
5. Review recent migrations: `alembic history`

---

## Important Notes

### Database
- Uses **PostgreSQL** in production
- Falls back to **SQLite** locally
- All migrations tracked in `alembic/versions/`
- Fixed multiple heads issue - see `ALEMBIC_MULTIPLE_HEADS_FIX.md`

### Authentication
- JWT-based authentication
- Role-based access control (RBAC)
- User scopes and permissions
- OAuth2 support

### Performance
- Async/await throughout
- Connection pooling
- Query optimization
- Caching layer ready

### Security
- Input validation (Pydantic v2)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- API rate limiting
- Encryption support

### Error Handling
- Comprehensive error responses
- Sentry error tracking
- Graceful degradation
- Audit trail of failures

---

## Documentation Files Generated

The following documentation also exists in the project:

- `VALHALLA_COMPLETE_SYSTEM_STATUS.md` - Complete system status
- `API_ENDPOINTS_LIVE.md` - Live endpoint documentation
- `CODEBASE_STRUCTURE_MAPPING.md` - Detailed code structure
- `DEPLOYMENT_GUIDE_20_MODULES.md` - Deployment procedures
- `DEV_WORKFLOW.md` - Development workflow
- `DEV_TEAM_QUICK_REFERENCE.md` - Quick reference
- `EXECUTIVE_SUMMARY.md` - High-level overview

Multiple **PACK_*.md** files document feature implementations organized by packs.

---

## Quick Reference Commands

```bash
# Install
pip install -r requirements.txt

# Dev server
uvicorn app.main:app --reload --port 4000

# Format
black . && isort .

# Lint
ruff check .

# Type check
mypy .

# Test
pytest -q

# Migrate DB
alembic upgrade head

# New migration
alembic revision --autogenerate -m "description"

# View API docs
curl http://localhost:4000/docs
```

---

## Support & Troubleshooting

### Common Issues

**Issue: Database connection fails**
- Check `DATABASE_URL` environment variable
- Ensure PostgreSQL is running
- Check network connectivity
- See `DATABASE_HARDENING_COMPLETE.md`

**Issue: Router not loading**
- Ensure router exports a `router` variable
- Check imports in `models/__init__.py`
- Verify no circular imports
- Check logs: `GET /logs`

**Issue: Tests failing**
- Run locally first: `pytest tests/test_file.py -v`
- Check database is initialized
- Review test configuration in `conftest.py`

**Issue: Migrations conflict**
- Review `ALEMBIC_FIX_FINAL.md`
- Check for multiple heads: `alembic branches`
- Merge heads if needed

---

## Version Information

- **FastAPI:** 0.115.0
- **Python:** 3.8+
- **SQLAlchemy:** 2.0.35
- **Pydantic:** 2.9.2
- **PostgreSQL:** 12+
- **Uvicorn:** 0.30.6

---

## Project Status

✅ **System Complete** - All major features implemented  
✅ **Database Schema** - Finalized and normalized  
✅ **API Endpoints** - 350+ endpoints live  
✅ **Security** - Full compliance measures  
✅ **Monitoring** - Health checks and observability  
✅ **Testing** - Comprehensive test coverage  
✅ **Documentation** - Complete  
✅ **Deployment** - Production-ready  

---

**Last Updated:** April 12, 2026  
**For Questions:** Contact your development lead

