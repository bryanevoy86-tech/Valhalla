# Complete Python Codebase Structure Mapping

**Last Updated:** March 26, 2026  
**Workspace Root:** `d:\dev`

---

## EXECUTIVE SUMMARY

The codebase has **3 parallel application spines** with **2 redundant copies**:

| Spine | Type | Status | Purpose |
|-------|------|--------|---------|
| `/dev/app/` | Thin Wrapper | **ACTIVE** | Entry point proxy to canonical system |
| `/dev/services/api/app/` | Canonical Backend | **ACTIVE** | Real implementation (100+ modules) |
| `/dev/backend/` | Legacy System | INACTIVE | Old implementation (being phased out) |
| `/dev/backend/app/` | Legacy Backend | LEGACY | Intermediate structure (superseded) |
| `/dev/valhalla/` | Full Mirror | TEST/ARCHIVE | Complete copy of entire `/dev/` structure |

**Canonical System:** `/dev/services/api/app/` ✅

---

## 1. ENTRY POINTS (main.py FILES)

### 🔴 **ACTIVE ENTRY POINT: `/dev/app/main.py`**
```
Path: d:\dev\app\main.py
Lines: ~30 lines
Purpose: THIN WRAPPER - Redirects to real backend
Link: imports from services.api.app.main
Status: ACTIVE - Used by "Run (dev)" task
```

**Content:**
```python
"""Thin application entrypoint for Valhalla.
⚠️ DO NOT add routers or middleware here.
This file ONLY re-exports the real FastAPI app.
The real HTTP app lives in: services/api/app/main.py
"""
sys.modules['app'] = import_module("services.api.app")
from services.api.app.main import app
```

**Execution:** `uvicorn app.main:app --reload --port 4000`

---

### 🟡 **REAL IMPLEMENTATION: `/dev/services/api/app/main.py`**
```
Path: d:\dev\services\api\app\main.py
Lines: ~1800+ lines
Purpose: CANONICAL BACKEND - Complete FastAPI application
Status: ACTIVE - Contains all real logic
```

**Key Features:**
- Full lifespan context manager (startup/shutdown)
- Comprehensive middleware stack:
  - CorrelationIdMiddleware
  - ReadOnlyShieldMiddleware
  - GoLiveMiddleware
  - ExecutionClassMiddleware
- Error handler registration
- Router registry integration
- 180+ dynamic route includes

---

### 🟠 **LEGACY: `/dev/backend/main.py`**
```
Path: d:\dev\backend\main.py
Lines: ~1000+ lines
Purpose: OLD SYSTEM - Heimdall/Admin routes
Status: INACTIVE - Legacy endpoints only
```

**Key Endpoints (not active in running system):**
- `/admin/heimdall/api/autopr/status`
- `/admin/heimdall/autopr/run`
- `/admin/heimdall/api/alerts/status`
- Queue management endpoints (pause/resume)
- Task validation endpoints

**Problem:** Mixes business logic with admin functions. Has direct psycopg2 imports, not ORM-based.

---

### 🟠 **LEGACY: `/dev/backend/app/main.py`**
```
Path: d:\dev\backend\app\main.py
Lines: ~50 lines
Purpose: INTERMEDIATE STRUCTURE - Simple FastAPI app
Status: SUPERSEDED - Not used in running system
```

**Content:**
```python
from .core.config import get_settings
from .core.db import Base, engine
from .core_gov.telemetry.logger import configure_logging
from .models import deal, lead, user  # noqa: F401

app = FastAPI(title=get_settings().PROJECT_NAME)
configure_logging()
```

**Issue:** Creates app but not used anywhere. Configs point to different locations than canonical system.

---

### 🟡 **MIRROR: `/dev/valhalla/app/main.py` & `/dev/valhalla/services/api/app/main.py`**
```
Path: d:\dev\valhalla\services\api\app\main.py
Type: DUPLICATE of canonical system
Status: TEST/ARCHIVE STRUCTURE
```

---

## 2. DATABASE CONNECTION FILES

### 🟡 **ACTIVE: `/dev/services/api/app/db.py`**
```
Path: d:\dev\services\api\app\db.py
Type: COMPATIBILITY SHIM
Purpose: Provides backward-compatible imports
```

**Content:**
```python
"""Compatibility shim. 
Some packs import `app.db` from older structure.
We now keep DB plumbing in `app.core.db`
"""
from app.core.db import engine, SessionLocal, get_db_session, get_db
```

**Real DB logic:** `/dev/services/api/app/core/db.py`

---

### 🟢 **REAL DB CONFIG: `/dev/services/api/app/core/db.py`**
```
Path: d:\dev\services\api\app\core\db.py
Type: SQLAlchemy Configuration
Purpose: ORM engine, session management
Status: ACTIVE - Used by all routers
```

**Configuration includes:**
```python
config.py - Database URL and connection settings
dependencies.py - DB session injection
engine - Connection pool
SessionLocal - Session factory
```

---

### 🟠 **LEGACY: `/dev/backend/db.py`**
```
Path: d:\dev\backend\db.py
Type: Direct psycopg2 connection
```

**Content:**
```python
def get_conn(dsn: Optional[str] = None):
    """Returns a psycopg2 connection with autocommit=True"""
    dsn = dsn or os.getenv("DATABASE_URL", "...")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    return conn
```

**Problem:** Raw SQL connections, no ORM. Completely different from active system.

---

### 🟠 **LEGACY: `/dev/backend/app/core/db.py`**
```
Path: d:\dev\backend\app\core\db.py
Type: SQLAlchemy Configuration (old)
Status: Legacy structure
```

**Differences from canonical:**
- Different auth module paths
- Different policy locations
- Deprecated event handlers

---

## 3. MODELS (DATA STRUCTURES)

### 🔴 THIN WRAPPER: `/dev/app/models/` (4 files)
```
education_engine.py
governance_decision.py
media_engine.py
story_engine.py
```
**Type:** Redirects/wrappers

---

### 🟠 LEGACY: `/dev/backend/app/models/` (18 files)
```
alert.py
audit_log.py
billing.py
buyer.py          ← Basic domain objects
deal.py
export_jobs.py
feature_flag.py
files.py
funfund.py
io_job.py
jobs.py
lead.py
notification.py
org.py
saved_chart.py
saved_view.py
shield.py
user.py
```
**Status:** Superseded - Old domain model

---

### 🟢 **CANONICAL: `/dev/services/api/app/models/` (180+ files)**

**Core Domain Models:**
```
deal.py                          ← Real estate transactions
lead.py                          ← Lead management
user.py                          ← Users/Auth
buyer.py                         ← Buyer profiles
contract_record.py               ← Contract tracking
```

**Financial Models:**
```
arbitrage_opportunity.py
arbitrage_profile.py
capital.py
capital_allocation.py
cost_model.py
revenue_ledger.py
risk_ledger.py
tax_risk_profile.py
wealth_allocation.py
```

**Governance Models (Empire System):**
```
empire_governance.py
empire_journal.py
empire_snapshot.py
decision_governance.py
decision_outcome.py
decision_recommendation.py
governance_decision.py
governance_settings.py
```

**AI/ML Models:**
```
ai_persona.py
ai_training_job.py
brain_state.py
education_engine.py
story_engine.py
media_engine.py
```

**Operational Models:**
```
error_log.py
event_log.py
system_status.py
system_health.py
telemetry_event.py
audit_event.py
```

**Specialized Domains (40+ additional):**
```
education_org.py                 ← Education pipeline
household.py                     ← Household profiles
rental_property.py               ← Real estate management
wholesale_deals.py               ← Wholesale structures
trust_residency.py               ← Trust/accounting
kids_education_tj.py            ← Children education
market_feed_event.py             ← Market data
scenario_simulator.py            ← Simulation engine
```

**TOTAL: 180+ domain models covering complete business logic**

---

## 4. ROUTERS (API ENDPOINTS)

### 🔴 THIN WRAPPER: `/dev/app/routers/` (11 files)
```
education_engine.py
engine_admin.py
example_guarded_endpoints.py
governance_decisions.py
intake.py
intake_admin.py
media_engine.py
metrics.py
outcomes.py
runbook_status.py
story_engine.py
```
**Type:** Simple wrapper routers

---

### 🟠 LEGACY: `/dev/backend/app/routers/` (16 files)
```
admin.py
admin_alerts.py
admin_bluegreen.py
admin_canary.py
admin_health.py
admin_observability.py
admin_replay.py
admin_sla.py
audit.py
billing.py
files.py
funfund.py
health.py
io.py
reporting.py
search.py
shield.py
```
**Type:** Admin-focused, limited scope

---

### 🟢 **CANONICAL: `/dev/services/api/app/routers/` (200+ routers)**

**Admin/Operations Routers:**
```
admin.py
admin_alerts.py
admin_bootstrap.py
admin_build.py
admin_dashboard.py
admin_go_live.py
admin_handoff.py
admin_healthcheck.py
admin_heimdall.py
admin_logs.py
admin_ops.py
admin_privacy.py
admin_secscan.py
admin_system_summary.py
admin_todo.py
```

**Domain-Specific Routers:**
```
deals.py                         ← Deal management (CRUD + lifecycle)
deal_analyzer.py
deal_finalization.py
deal_lifecycle.py
deal_workflow_status.py
```

```
leads.py
lead_engine.py
leads_status.py
```

```
buyers.py
buyer_match.py
buyer_liquidity.py
contracts.py
contracts_lifecycle.py
contracts_pipeline.py
```

**Governance/Decision System Routers:**
```
governance_decisions.py
governance_orchestrator.py
governance_policy.py
governance_king.py
governance_loki.py
governance_odin.py
governance_queen.py
governance_tyr.py
decision_governance.py
decision_outcome.py
decision_recommendation.py
```

**Financial Routers:**
```
arbitrage.py
capital.py
credit_card_spending.py
finops.py
income_routing.py
ledger.py
payments.py
revenue_ledger.py
risk.py
tax_bridge.py
tax_tracker.py
```

**Operational Routers:**
```
analytics.py
audit.py
compliance.py
event_log.py
exports_month.py
exports_packs.py
feature_flags.py
health.py
metrics.py
notifications.py
reporting.py
```

**AI/Inference Routers:**
```
brain_state.py
education_engine.py
media_engine.py
story_engine.py
```

**System/Infrastructure Routers:**
```
go_live.py
floor_control.py
security.py
security_dashboard.py
system_config.py
system_health.py
system_log.py
system_selftest.py
system_status.py
```

**TOTAL: 200+ routers with full REST API coverage**

---

## 5. SERVICES (Business Logic Layer)

### 🔴 THIN WRAPPER: `/dev/app/services/` (4 files)
```
education_engine.py
governance_service.py
media_engine.py
story_engine.py
```

---

### 🟠 LEGACY: `/dev/backend/app/services/` (16 files)
```
admin.py
ai/                              ← AI service directory
audit.py
billing.py
buyer_matcher.py
csv_utils.py
funfund.py
io_jobs.py
mailer.py
metrics.py
notifications.py
query_builder.py
reporting.py
s3.py
underwriting.py
webhooks.py
```

---

### 🟢 **CANONICAL: `/dev/services/api/app/services/` (140+ files)**

**Core Services:**
```
deal_finalization.py
decision_governance.py
decision_outcome.py
decision_recommendation.py
lead_service.py
customer_service.py              (implied)
```

**Integration Services:**
```
api_clients.py
email_service.py
notification_bridge.py
notification_channel.py
notification_orchestrator.py
webhooks.py                       (in routers)
```

**Calculation/Analysis Services:**
```
analytics_engine.py
banking_structure_planner.py
blueprint_service.py
buyer_liquidity.py
capital_allocation_service.py
cost_model_service.py
curriculum_builder_service.py
data_io_service.py
data_lineage.py
data_retention.py
deal_finalization.py
education_assessment_service.py
export_job.py
financial_stress.py
```

**Governance/Decision Services:**
```
governance_service.py
heimdall_governance.py
heimdall_ultra.py
heimdall_workload.py
empire_governance.py
empire_journal.py
```

**AI/ML Services:**
```
brain_state.py
clone_engine_service.py
curriculum_builder_service.py
education_engine.py
education_org_service.py
education_student_service.py
explanation_engine.py
media_engine.py
narrative.py
story_engine.py
story_mode.py
story_video_service.py
```

**Storage/Data Services:**
```
daily_rhythm.py
data_io_service.py
data_lineage.py
data_retention.py
event_log.py
integrity_monitor.py
system_health.py
system_log.py
```

**Specialized Domain Services (50+):**
```
lead_service.py
underwriting_engine.py
wholesale_engine.py
rental_property_service.py       (implied from models)
household_service.py
hr_service.py
kids_education.py
legal_drafting_service.py
maintenance.py
market_policy.py
mental_load.py
```

**TOTAL: 140+ service files implementing all business logic**

---

## 6. CORE INFRASTRUCTURE

### 🔴 THIN WRAPPER: `/dev/app/core/` (3 items)
```
config/         ← Simple config
core/ directory
data/
```

---

### 🟠 LEGACY: `/dev/backend/app/core/` (8 files)
```
auth/
config.py
db.py
events.py          ← Old event handlers
exports/           ← Export utilities
health/
models.py          ← Compatibility models
policy/
security.py
```

---

### 🟢 **CANONICAL: `/dev/services/api/app/core/` (40+ files)**

**Configuration:**
```
config.py                        ← Main settings
correlation_middleware.py        ← Request tracing
dependencies.py                  ← Dependency injection
```

**Database:**
```
db.py                            ← ORM configuration
contract_render.py               ← Contract templating
```

**Middleware:**
```
correlation_middleware.py        ← Request ID tracking
execution_class_middleware.py    ← Execution context
go_live_middleware.py            ← Feature gate
read_only_middleware.py          ← Safety guard
```

**Core Logic:**
```
engine_guard.py                  ← Engine safeguards
error_handling.py                ← Exception handling
execution_class.py               ← Execution context
god_arbitrator.py                ← Decision arbitration
heimdall_guard_helpers.py        ← Guard helpers
```

**Runtime:**
```
kpi_helpers.py                   ← KPI calculation
loki_engine.py                   ← Observability
matcher.py                       ← Matching logic
normalizer.py                    ← Data normalization
router_registry.py               ← Dynamic router loading
runtime_flags.py                 ← Feature flags
```

**Security/Policy:**
```
policy/                          ← Policy definitions
prelaunch/                       ← Pre-deployment checks
git_utils.py                     ← Git integration
security.py                      ← Auth/RBAC
```

---

## 7. SCHEMAS (Data Validation/Serialization)

### 🔴 THIN WRAPPER: `/dev/app/schemas/` (Not listed)

### 🟠 LEGACY: `/dev/backend/app/schemas/` (Basic ORM models)

### 🟢 **CANONICAL: `/dev/services/api/app/schemas/` (Pydantic models)**
- Input/output validation for all API endpoints
- OpenAPI schema generation
- Type safety for all routers
- Response/request serialization

---

## 8. DIRECTORY STRUCTURE COMPARISON

### Three Parallel Spines Visualized:

```
SPINE 1: THIN WRAPPER (ACTIVE PROXY)
d:\dev\app\
├── main.py                          ← Entry point (uvicorn app.main:app)
├── models\                          ← 4 files (wrappers)
├── routers\                         ← 11 files (redirects)
├── schemas\                         ← Thin wrappers
├── services\                        ← 4 files (redirects)
├── core\                            ← Minimal config
└── [imports from services.api.app]  ← Explicitly imports canonical

SPINE 2: CANONICAL BACKEND (REAL SYSTEM) ⭐
d:\dev\services\api\app\
├── main.py                          ← Real FastAPI app (1800+ lines)
├── models\                          ← 180+ domain models
├── routers\                         ← 200+ API endpoints
├── schemas\                         ← Full validation layer
├── services\                        ← 140+ business logic files
├── core\                            ← 40+ infrastructure files
├── middleware\                      ← Safety/governance
├── observability\                   ← Logging/telemetry
├── db.py                            ← Compatibility shim
├── db\                              ← Database layer
├── accounting\                      ← Domain specialization
├── deals\                           ← Domain specialization
├── leads\                           ← Domain specialization
├── banking\                         ← Domain specialization
├── compliance\                      ← Domain specialization
├── governance\                      ← Domain specialization
├── heimdall\                        ← Guard system
├── ui_dashboard\                    ← UI backend
├── workflows\                       ← Workflow engine
└── [100+ domain-specific modules]   ← Complete business system

SPINE 3: LEGACY SYSTEM (INACTIVE)
d:\dev\backend\
├── main.py                          ← Old entry point (not used)
│   ├── Imports from backend.* namespace
│   ├── Heimdall/admin routes only
│   └── Direct psycopg2 connections
├── db.py                            ← Legacy raw SQL connections
├── app\main.py                      ← Intermediate structure
├── app\core\db.py                   ← Old ORM config
├── app\models\                      ← 18 legacy domain models
├── app\routers\                     ← 16 admin-focused routers
├── app\services\                    ← 16 limited services
└── [Not used in running system]     ← Completely superseded

SPINE 4: FULL MIRROR (TEST/ARCHIVE)
d:\dev\valhalla\
├── [Complete mirror of d:\dev\]     ← Full copy of both spines
└── [May be out of sync]             ← Archive/test structure
```

---

## 9. IMPORTS ANALYSIS

### Pattern 1: Thin Wrapper (app/)
```python
# d:\dev\app\main.py
from services.api.app.main import app

# This is the ONLY import needed
# No local business logic
```

### Pattern 2: Real System (services/api/app/)
```python
# d:\dev\services\api\app\main.py
from app.core.db import verify_schema_initialized
from app.core.settings import settings
from app.middleware.safety import safety_guard
# ... 1800+ lines of real logic ...
from app.core.router_registry import include_router_safe

# Contains ALL the business logic
# Uses 'app' module name (injected into sys.modules by wrapper)
```

### Pattern 3: Legacy System (backend/)
```python
# d:\dev\backend\main.py
from backend.notify import post_discord
from backend.db import get_conn
from backend.heimdall_service import (...)
# ... mixes concerns ...

# NEVER imports from the canonical system
# Uses 'backend' namespace exclusively
# NOT USED in production
```

---

## 10. DUPLICATE/REDUNDANT STRUCTURES

### ✅ NECESSARY DUPLICATES:
- `/dev/app/` → `/dev/services/api/app/` (intentional proxy pattern)
- `/dev/backend/app/db.py` → `/dev/services/api/app/core/db.py` (backward compatibility shim)

### ❌ UNNECESSARY DUPLICATES TO CONSOLIDATE:
1. `/dev/backend/` - ENTIRELY LEGACY
   - No imports from it in active system
   - Not called by any routing
   - Can be archived/deleted

2. `/dev/backend/app/` - INTERMEDIATE STRUCTURE
   - Models not used (superseded by service models)
   - Routes not registered (not imported in main.py)
   - Services replaced by full service layer
   - Can be deleted

3. `/dev/valhalla/` - MIRROR STRUCTURE
   - Appears to be copy for testing/backup
   - If not actively used, can be archived
   - Increases maintenance burden

---

## 11. ACTIVE VS LEGACY STATUS

### ✅ ACTIVE PRODUCTION COMPONENTS:

| Component | Location | Status | Evidence |
|-----------|----------|--------|----------|
| **Entry Point** | `/dev/app/main.py` | Active | Run task: `uvicorn app.main:app` |
| **FastAPI App** | `/dev/services/api/app/main.py` | Active | Explicitly imported by wrapper |
| **Models** | `/dev/services/api/app/models/` | Active | Used in all routers |
| **Routers** | `/dev/services/api/app/routers/` | Active | Included in main.py (line 1778+) |
| **Services** | `/dev/services/api/app/services/` | Active | Called by routers |
| **Core Config** | `/dev/services/api/app/core/` | Active | All middleware, middleware, DB configured here |
| **Database** | `/dev/services/api/app/core/db.py` | Active | ORM SessionLocal factory |

### ❌ INACTIVE/LEGACY COMPONENTS:

| Component | Location | Status | Evidence |
|-----------|----------|--------|----------|
| **Backend App** | `/dev/backend/main.py` | Inactive | Not imported anywhere |
| **Backend DB** | `/dev/backend/db.py` | Inactive | Uses psycopg2 not ORM |
| **Backend App** | `/dev/backend/app/main.py` | Legacy | No imports from canonical system |
| **Backend Models** | `/dev/backend/app/models/` | Obsolete | Only 18 files vs 180+ in canonical |
| **Backend Routers** | `/dev/backend/app/routers/` | Obsolete | Not registered in active app |
| **Backend Services** | `/dev/backend/app/services/` | Obsolete | Not called in canonical system |
| **Valhalla Copy** | `/dev/valhalla/` | Archive | Mirror of entire structure |

---

## 12. CONSOLIDATION ROADMAP

### Phase 1: Verification
- [ ] Confirm `/dev/backend/` is never imported by active system
- [ ] Verify all routes are loaded from `/dev/services/api/app/routers/`
- [ ] Check for any remaining imports from `backend.` in canonical system

### Phase 2: Archive Legacy
- [ ] Move `/dev/backend/` to `.archive/backend_legacy_v1`
- [ ] Move `/dev/valhalla/` to `.archive/valhalla_mirror_v1`
- [ ] Update documentation

### Phase 3: Cleanup Thin Wrapper
- Consider making `/dev/app/` even thinner if possible
- Or consolidate sys.modules injection elsewhere

### Phase 4: Documentation
- [ ] Update deployment docs to point to canonical system
- [ ] Document why wrapper exists (for sys.modules aliasing)
- [ ] Update architecture diagrams

---

## 13. KEY METRICS

| Metric | Thin Wrapper | Canonical System | Legacy System |
|--------|--------------|------------------|---------------|
| **main.py size** | ~30 lines | ~1800 lines | ~1000+ lines |
| **Models** | 4 files | 180+ files | 18 files |
| **Routers** | 11 files | 200+ files | 16 files |
| **Services** | 4 files | 140+ files | 16 files |
| **Domain Coverage** | Minimal | Complete | Limited |
| **Status** | Proxy | Production | Deprecated |

---

## 14. IMPORTS THAT PROVE STRUCTURE

### Definitive Evidence - Canonical System Uses:
```python
# From d:\dev\services\api\app\main.py line 13
from app.core.db import verify_schema_initialized

# From d:\dev\services\api\app\main.py line 147
from app.core.correlation_middleware import CorrelationIdMiddleware

# From d:\dev\services\api\app\main.py line 1778
from app.core.prelaunch.alerts_engine.router import router as alerts_router
```

### Definitive Evidence - Wrapper Redirects:
```python
# From d:\dev\app\main.py line 22
from services.api.app.main import app
```

### Definitive Evidence - Legacy System Unused:
```python
# From d:\dev\backend\main.py (lines 43, 136, 228, etc.)
from backend.notify import post_discord
from backend.db import get_conn
from backend.heimdall_service import ...
# NOT imported anywhere in canonical system
```

---

## CONCLUSION

The codebase has successfully evolved to a **canonical microarchitecture**:

1. **Thin Entry Point:** `/dev/app/` - Minimal proxy using sys.modules aliasing
2. **Real Backend:** `/dev/services/api/app/` - Complete 300+ module system
3. **Legacy Cruft:** `/dev/backend/` - Unused, can be archived

**Immediate Action:** All development and consolidation should target `/dev/services/api/app/` as the single source of truth.

