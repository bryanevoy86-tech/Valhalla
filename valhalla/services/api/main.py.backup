import os
import sys

# PYTHONPATH is set to /app/services/api in Dockerfile, so app.* imports work directly
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.telemetry.middleware import TelemetryExceptionMiddleware
from app.metrics.middleware import MetricsMiddleware

from app.core.settings import settings

# Core routers (should always be available)
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.capital import router as capital_router
from app.routers.telemetry import router as telemetry_router
from app.routers.admin import router as admin_router
from app.routers.ui_dashboard import router as ui_dashboard_router
from app.routers.system_health import router as system_health_router
from app.routers.analytics import router as analytics_router
from app.routers.alerts import router as alerts_router
from app.routers.roles import router as roles_router
from app.routers.debug_runtime import router as debug_runtime_router
from app.routers.admin_heimdall import router as admin_heimdall_router
from app.routers.admin_system_summary import router as admin_system_summary_router
from app.routers.admin_dependencies import router as admin_dependencies_router
from app.routers.admin_dashboard import router as admin_dashboard_router
from app.routers.admin_healthcheck import router as admin_healthcheck_router
from app.routers.admin_bootstrap import router as admin_bootstrap_router
from app.routers.admin_todo import router as admin_todo_router

# PACK S: System introspection (debug endpoints)
from app.routers.debug_system import router as debug_system_router

# PACK T: Production hardening (security, rate limiting, logging)
from app.middleware.security import SecurityHeadersMiddleware, SimpleRateLimitMiddleware
from app.middleware.logging import RequestLoggingMiddleware

# PACK U: Frontend preparation (UI map for WeWeb)
from app.routers.ui_map import router as ui_map_router

# PACK V: Deployment checklist (ops automation)
from app.routers.deploy_check import router as deploy_check_router

# PACK TM, TN, TO: Philosophy, Relationships, Daily Rhythm
from app.routers.philosophy import router as philosophy_router
from app.routers.relationships import router as relationships_router
from app.routers.daily_rhythm import router as daily_rhythm_router

# Pack routers with error handling
GRANTS_AVAILABLE = False
BUYERS_AVAILABLE = False
DEALS_AVAILABLE = False
MATCH_AVAILABLE = False
CONTRACTS_AVAILABLE = False
INTAKE_AVAILABLE = False
NOTIFY_AVAILABLE = False
MESSAGING_AVAILABLE = False
PAYMENTS_AVAILABLE = False
NEGOTIATIONS_AVAILABLE = False
RBAC_AVAILABLE = False
INFLUENCE_AVAILABLE = False
NEGOTIATION_STRATEGIES_AVAILABLE = False
LEADS_AVAILABLE = False
ADVANCED_NEGOTIATION_AVAILABLE = False
BEHAVIORAL_PROFILING_AVAILABLE = False
DEAL_ANALYZER_AVAILABLE = False
CLOSERS_AVAILABLE = False
WORKFLOWS_AVAILABLE = False
AUDIT_AVAILABLE = False
FREEZE_AVAILABLE = False
KNOWLEDGE_AVAILABLE = False
SCHEDULED_JOBS_AVAILABLE = False
COMPLIANCE_AVAILABLE = False
ORCHESTRATOR_AVAILABLE = False
FINOPS_AVAILABLE = False
ARBITRAGE_AVAILABLE = False
DOCS_AVAILABLE = False
POLICIES_AVAILABLE = False
PROVIDERS_AVAILABLE = False
BEHAVIOR_AVAILABLE = False
BRRRR_AVAILABLE = False
ACCOUNTING_AVAILABLE = False
LEGAL_AVAILABLE = False
NEG_ENHANCE_AVAILABLE = False
BLACK_ICE_AVAILABLE = False
CHILDREN_AVAILABLE = False
QUEEN_AVAILABLE = False
KING_AVAILABLE = False
PANTRY_AVAILABLE = False
RESORT_AVAILABLE = False
INTEGRITY_AVAILABLE = False
TAX_AVAILABLE = False
HEIMDALL_TRAINING_AVAILABLE = False
UNDERWRITER_AVAILABLE = False
CLOSER_ENGINE_AVAILABLE = False
CONTRACT_ENGINE_AVAILABLE = False
BUYER_MATCH_AVAILABLE = False
FLOW_LEAD_TO_DEAL_AVAILABLE = False
UNDERWRITING_ENGINE_AVAILABLE = False
FLOW_FULL_PIPELINE_AVAILABLE = False
DEAL_WORKFLOW_STATUS_AVAILABLE = False
FLOW_PREPARE_CLOSING_AVAILABLE = False
CLOSING_PLAYBOOK_AVAILABLE = False
FLOW_NOTIFICATIONS_AVAILABLE = False
FLOW_PROFIT_ALLOCATION_AVAILABLE = False

try:
    from app.routers.grants import router as grants_router
    GRANTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import grants router: {e}")
    grants_router = None

try:
    from app.routers.buyers import router as buyers_router
    BUYERS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import buyers router: {e}")
    buyers_router = None

try:
    from app.routers.deals import router as deals_router
    DEALS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import deals router: {e}")
    deals_router = None

try:
    from app.routers.match import router as match_router
    MATCH_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import match router: {e}")
    match_router = None

try:
    from app.routers.contracts import router as contracts_router
    CONTRACTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import contracts router: {e}")
    contracts_router = None

try:
    from app.routers.intake import router as intake_router
    INTAKE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import intake router: {e}")
    intake_router = None

try:
    from app.routers.notify import router as notify_router
    NOTIFY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import notify router: {e}")
    notify_router = None

# Messaging router (Pack 26) — optional import
try:
    from app.routers.messaging import router as messaging_router
    MESSAGING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import messaging router: {e}")
    messaging_router = None

# Payments router (Pack 27) — optional import
try:
    from app.routers.payments import router as payments_router
    PAYMENTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import payments router: {e}")
    payments_router = None

# Negotiations router (Pack 28) — optional import
try:
    from app.routers.negotiations import router as negotiations_router
    NEGOTIATIONS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import negotiations router: {e}")
    negotiations_router = None

# Try importing RBAC router (Pack 25)
try:
    from app.routers.rbac import router as rbac_router
    RBAC_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import RBAC router: {e}")
    RBAC_AVAILABLE = False
    rbac_router = None

# Influence router (Pack 29) — optional import
try:
    from app.routers.influence import router as influence_router
    INFLUENCE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import influence router: {e}")
    influence_router = None

# Negotiation Strategies router (Pack 30) — optional import
try:
    from app.routers.negotiation_strategies import router as negotiation_strategies_router
    NEGOTIATION_STRATEGIES_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import negotiation-strategies router: {e}")
    negotiation_strategies_router = None

# Leads router (Pack 31) — optional import
try:
    from app.routers.leads import router as leads_router
    LEADS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import leads router: {e}")
    leads_router = None

# Advanced Negotiation Techniques router (Pack 32) — optional import
try:
    from app.routers.advanced_negotiation_techniques import router as advanced_negotiation_router
    ADVANCED_NEGOTIATION_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import advanced-negotiation-techniques router: {e}")
    advanced_negotiation_router = None

# Behavioral Profiling router (Pack 33) — optional import
try:
    from app.routers.behavioral_profiles import router as behavioral_profiling_router
    BEHAVIORAL_PROFILING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import behavioral-profiling router: {e}")
    behavioral_profiling_router = None

# Deal Analyzer router (Pack 34) — optional import
try:
    from app.routers.deal_analyzer import router as deal_analyzer_router
    DEAL_ANALYZER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import deal-analyzer router: {e}")
    deal_analyzer_router = None

# AI Closers router (Pack 35) — optional import
try:
    from app.routers.closers import router as closers_router
    CLOSERS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import ai-closers router: {e}")
    closers_router = None

# Workflows router (Pack 36) — optional import
try:
    from app.routers.workflows import router as workflows_router
    WORKFLOWS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import workflows router: {e}")
    workflows_router = None

# Integrity Ledger / Audit router (Pack 37)
try:
    from app.routers.audit import router as audit_router
    AUDIT_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import audit router: {e}")
    audit_router = None

# Freeze Rules router (Pack 38)
try:
    from app.routers.freeze import router as freeze_router
    FREEZE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import freeze router: {e}")
    freeze_router = None

# Knowledge router (Pack 39)
try:
    from app.routers.knowledge import router as knowledge_router
    KNOWLEDGE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import knowledge router: {e}")
    knowledge_router = None

# Scheduled Jobs router (Pack 40)
try:
    from app.routers.scheduled_jobs import router as scheduled_jobs_router
    SCHEDULED_JOBS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import scheduled-jobs router: {e}")
    scheduled_jobs_router = None

# Compliance router (Pack 41)
try:
    from app.routers.compliance import router as compliance_router
    COMPLIANCE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import compliance router: {e}")
    compliance_router = None

# Orchestrator router (Pack 42)
try:
    from app.routers.orchestrator import router as orchestrator_router
    ORCHESTRATOR_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import orchestrator router: {e}")
    orchestrator_router = None

# FinOps router (Pack 43)
try:
    from app.routers.finops import router as finops_router
    FINOPS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import finops router: {e}")
    finops_router = None

# Arbitrage router (Pack 44)
try:
    from app.routers.arbitrage import router as arbitrage_router
    ARBITRAGE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import arbitrage router: {e}")
    arbitrage_router = None

# Docs router (Pack 45)
try:
    from app.routers.docs import router as docs_router
    DOCS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import docs router: {e}")
    docs_router = None

# Policies router (Pack 46)
try:
    from app.routers.policies import router as policies_router
    POLICIES_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import policies router: {e}")
    policies_router = None

# Providers router (Pack 47)
try:
    from app.routers.providers import router as providers_router
    PROVIDERS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import providers router: {e}")
    providers_router = None

# Behavior router (Pack 48)
try:
    from app.routers.behavior import router as behavior_router
    BEHAVIOR_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import behavior router: {e}")
    behavior_router = None

# BRRRR router (Pack 49)
try:
    from app.routers.brrrr import router as brrrr_router
    BRRRR_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import brrrr router: {e}")
    brrrr_router = None

# Accounting router (Pack 50)
try:
    from app.routers.accounting import router as accounting_router
    ACCOUNTING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import accounting router: {e}")
    accounting_router = None

# Legal router (Pack 51)
try:
    from app.routers.legal import router as legal_router
    LEGAL_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import legal router: {e}")
    legal_router = None

# Black Ice router (Pack 53)
try:
    from app.routers.blackice import router as blackice_router
    BLACK_ICE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import blackice router: {e}")
    blackice_router = None

# Children router (Pack 54)
try:
    from app.routers.children import router as children_router
    CHILDREN_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import children router: {e}")
    children_router = None

# Queen router (Pack 55)
try:
    from app.routers.queen import router as queen_router
    QUEEN_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import queen router: {e}")
    queen_router = None

# King router (Pack 56)
try:
    from app.routers.king import router as king_router
    KING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import king router: {e}")
    king_router = None

# Pantry router (Pack 57)
try:
    from app.routers.pantry import router as pantry_router
    PANTRY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import pantry router: {e}")
    pantry_router = None

# Resort router (Pack 58)
try:
    from app.routers.resort import router as resort_router
    RESORT_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import resort router: {e}")
    resort_router = None

# Integrity router (Pack 59)
try:
    from app.routers.integrity import router as integrity_router
    INTEGRITY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import integrity router: {e}")
    integrity_router = None

# Tax tracker router (Pack 60)
try:
    from app.routers.tax_tracker import router as tax_tracker_router
    TAX_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import tax tracker router: {e}")
    tax_tracker_router = None

# Heimdall training router (Pack 61)
try:
    from app.routers.heimdall_training import router as heimdall_training_router
    HEIMDALL_TRAINING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import heimdall training router: {e}")
    heimdall_training_router = None

# Underwriter router (Pack 62)
try:
    from app.routers.underwriter import router as underwriter_router
    UNDERWRITER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import underwriter router: {e}")
    underwriter_router = None

# Closer Engine router (Pack 63)
try:
    from app.routers.closer_engine import router as closer_engine_router
    CLOSER_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import closer engine router: {e}")
    closer_engine_router = None

# Contract Engine router (Pack 64)
try:
    from app.routers.contract_engine import router as contract_engine_router
    CONTRACT_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import contract engine router: {e}")
    contract_engine_router = None

# Buyer Match router (Pack 65)
try:
    from app.routers.buyer_match import router as buyer_match_router
    BUYER_MATCH_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import buyer match router: {e}")
    buyer_match_router = None

# Flow orchestrator - Lead to Deal (unified flow)
FLOW_LEAD_TO_DEAL_AVAILABLE = False
try:
    from app.routers.flow_lead_to_deal import router as flow_lead_to_deal_router
    FLOW_LEAD_TO_DEAL_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_lead_to_deal router: {e}")
    flow_lead_to_deal_router = None

# Underwriting Engine flow router
UNDERWRITING_ENGINE_AVAILABLE = False
try:
    from app.routers.underwriting_engine import router as underwriting_engine_router
    UNDERWRITING_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import underwriting_engine router: {e}")
    underwriting_engine_router = None

# Full Deal Pipeline flow router (combined lead + deal + underwriting + matching)
FLOW_FULL_PIPELINE_AVAILABLE = False
try:
    from app.routers.flow_full_pipeline import router as flow_full_pipeline_router
    FLOW_FULL_PIPELINE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_full_pipeline router: {e}")
    flow_full_pipeline_router = None

# Deal Workflow Status router
DEAL_WORKFLOW_STATUS_AVAILABLE = False
try:
    from app.routers.deal_workflow_status import router as deal_workflow_status_router
    DEAL_WORKFLOW_STATUS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import deal_workflow_status router: {e}")
    deal_workflow_status_router = None

# Flow Prepare Closing router (closing context builder)
FLOW_PREPARE_CLOSING_AVAILABLE = False
try:
    from app.routers.flow_prepare_closing import router as flow_prepare_closing_router
    FLOW_PREPARE_CLOSING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_prepare_closing router: {e}")
    flow_prepare_closing_router = None

# Closing Playbook router (closing script generator)
CLOSING_PLAYBOOK_AVAILABLE = False
try:
    from app.routers.closing_playbook import router as closing_playbook_router
    CLOSING_PLAYBOOK_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import closing_playbook router: {e}")
    closing_playbook_router = None

# Flow Notifications router (seller/buyer notifications builder)
FLOW_NOTIFICATIONS_AVAILABLE = False
try:
    from app.routers.flow_notifications import router as flow_notifications_router
    FLOW_NOTIFICATIONS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_notifications router: {e}")
    flow_notifications_router = None

# Flow Profit Allocation router (tax, FunFunds, reinvest calculations)
FLOW_PROFIT_ALLOCATION_AVAILABLE = False
try:
    from app.routers.flow_profit_allocation import router as flow_profit_allocation_router
    FLOW_PROFIT_ALLOCATION_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_profit_allocation router: {e}")
    flow_profit_allocation_router = None

# Deal Lifecycle Orchestrator router (unified control tower for deal pipeline)
DEAL_LIFECYCLE_AVAILABLE = False
try:
    from app.routers.deal_lifecycle import router as deal_lifecycle_router
    DEAL_LIFECYCLE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import deal_lifecycle router: {e}")
    deal_lifecycle_router = None

# FunFunds Planner router (monthly budgeting calculator)
FLOW_FUNFUNDS_PLANNER_AVAILABLE = False
try:
    from app.routers import flow_funfunds_planner
    FLOW_FUNFUNDS_PLANNER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import flow_funfunds_planner router: {e}")
    flow_funfunds_planner = None

# Negotiation Enhancer router (Pack 52)
try:
    from app.routers.neg_enhance import router as neg_enhance_router
    NEG_ENHANCE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import negotiation enhancer router: {e}")
    neg_enhance_router = None

# Try importing builder router with error handling
try:
    from app.routers.builder import router as builder_router
    BUILDER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import builder router: {e}")
    BUILDER_AVAILABLE = False
    builder_router = None

# Try importing reports router (will be created by builder)
try:
    from app.routers.reports import router as reports_router
    REPORTS_AVAILABLE = True
except Exception as e:
    print(f"INFO: Reports router not yet available: {e}")
    REPORTS_AVAILABLE = False
    reports_router = None

# Try importing research and playbooks routers
try:
    from app.routers.research import router as research_router
    from app.routers.playbooks import router as playbooks_router
    from app.routers.jobs import router as jobs_router
    from app.routers.research_semantic import router as research_semantic_router
    RESEARCH_AVAILABLE = True
    RESEARCH_ERROR = None
except Exception as e:
    import traceback
    RESEARCH_ERROR = f"{str(e)}\n{traceback.format_exc()}"
    print(f"WARNING: Research/Playbooks/Jobs routers not available: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    RESEARCH_AVAILABLE = False
    research_router = None
    playbooks_router = None
    jobs_router = None
    research_semantic_router = None


app = FastAPI(title="Valhalla API", version="3.4")

# Heimdall build gate: always-on registration (must be after app creation)
# This ensures /governance/heimdall_build_request exists for both runtime and tests
from app.routers import heimdall_build_gate
app.include_router(heimdall_build_gate.router)

# Auto-create tables on startup (dev-friendly; controlled via AUTO_CREATE_SCHEMA env var)
try:
    from app.core.db import Base, engine
    from app.core.startup import should_auto_create_schema
    
    @app.on_event("startup")
    def startup_create_tables():
        try:
            if should_auto_create_schema():
                Base.metadata.create_all(bind=engine)
                print("AUTO_CREATE_SCHEMA enabled: Created tables if they didn't exist")
            else:
                print("AUTO_CREATE_SCHEMA disabled: Relying on Alembic migrations for schema management")
        except Exception as e:
            print(f"WARNING: Failed to auto-create tables on startup: {e}")
except Exception as e:
    print(f"INFO: Skipping auto-create tables setup: {e}")

# Background scheduler loop (Pack 40)
try:
    from app.scheduler.runner import scheduler_loop

    @app.on_event("startup")
    async def startup_scheduler():
        try:
            import asyncio as _asyncio
            _asyncio.create_task(scheduler_loop())
            print("[startup] Scheduler loop started")
        except Exception as _e:
            print(f"INFO: Could not start scheduler loop: {_e}")
except Exception as e:
    print(f"INFO: Scheduler not enabled: {e}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ALLOWED_ORIGINS", []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-API-Key"],
)

# Global exception telemetry (best-effort)
try:
    app.add_middleware(TelemetryExceptionMiddleware)
except Exception as _e:  # pragma: no cover
    print(f"INFO: TelemetryExceptionMiddleware not enabled: {_e}")

# Runtime metrics collection (best-effort)
try:
    app.add_middleware(MetricsMiddleware)
except Exception as _e:  # pragma: no cover
    print(f"INFO: MetricsMiddleware not enabled: {_e}")

# PACK T: Production hardening middleware
try:
    app.add_middleware(RequestLoggingMiddleware)
    print("INFO: Request logging middleware enabled")
except Exception as _e:
    print(f"INFO: Request logging middleware not enabled: {_e}")

try:
    app.add_middleware(SimpleRateLimitMiddleware)
    print("INFO: Rate limiting middleware enabled")
except Exception as _e:
    print(f"INFO: Rate limiting middleware not enabled: {_e}")

try:
    app.add_middleware(SecurityHeadersMiddleware)
    print("INFO: Security headers middleware enabled")
except Exception as _e:
    print(f"INFO: Security headers middleware not enabled: {_e}")

# Register routers (core routers always available)
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(ui_dashboard_router, prefix="/api")
app.include_router(system_health_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(debug_runtime_router)  # Debug runtime introspection
app.include_router(debug_system_router)  # PACK S: System introspection
app.include_router(ui_map_router)  # PACK U: UI map for WeWeb
app.include_router(deploy_check_router)  # PACK V: Deployment checks
app.include_router(philosophy_router)  # PACK TM: Core Philosophy Archive
app.include_router(relationships_router)  # PACK TN: Trust & Relationship Mapping
app.include_router(daily_rhythm_router)  # PACK TO: Daily Rhythm & Tempo
app.include_router(admin_heimdall_router)  # Heimdall admin controls
app.include_router(admin_system_summary_router)  # System overview panel

# Freeze Events router (Pack 126) — graceful degradation if table not available
try:
    from app.routers import freeze_events
    FREEZE_EVENTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import freeze_events router: {e}")
    freeze_events = None
    FREEZE_EVENTS_AVAILABLE = False

if FREEZE_EVENTS_AVAILABLE and freeze_events is not None:
    app.include_router(freeze_events.router)
    print("INFO: Freeze Events router registered")

# Admin Dependencies router — check for optional/required packages
try:
    ADMIN_DEPS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import admin_dependencies router: {e}")
    admin_dependencies_router = None
    ADMIN_DEPS_AVAILABLE = False

if ADMIN_DEPS_AVAILABLE:
    app.include_router(admin_dependencies_router)
    print("INFO: Admin Dependencies router registered")

# Admin Dashboard router — master system overview combining all metrics
try:
    ADMIN_DASHBOARD_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import admin_dashboard router: {e}")
    admin_dashboard_router = None
    ADMIN_DASHBOARD_AVAILABLE = False

if ADMIN_DASHBOARD_AVAILABLE and admin_dashboard_router is not None:
    app.include_router(admin_dashboard_router)
    print("INFO: Admin Dashboard router registered")

# Admin Healthcheck router — basic and deep health status
try:
    ADMIN_HEALTHCHECK_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import admin_healthcheck router: {e}")
    admin_healthcheck_router = None
    ADMIN_HEALTHCHECK_AVAILABLE = False

if ADMIN_HEALTHCHECK_AVAILABLE and admin_healthcheck_router is not None:
    app.include_router(admin_healthcheck_router)
    print("INFO: Admin Healthcheck router registered")

# Admin Bootstrap router — ordered checklist of setup steps
try:
    ADMIN_BOOTSTRAP_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import admin_bootstrap router: {e}")
    admin_bootstrap_router = None
    ADMIN_BOOTSTRAP_AVAILABLE = False

if ADMIN_BOOTSTRAP_AVAILABLE and admin_bootstrap_router is not None:
    app.include_router(admin_bootstrap_router)
    print("INFO: Admin Bootstrap router registered")

# Admin TODO router — structured task list for setup and development
try:
    ADMIN_TODO_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import admin_todo router: {e}")
    admin_todo_router = None
    ADMIN_TODO_AVAILABLE = False

if ADMIN_TODO_AVAILABLE and admin_todo_router is not None:
    app.include_router(admin_todo_router)
    print("INFO: Admin TODO router registered")

# Security router (Pack 17) — optional import to avoid startup failure if deps missing
try:
    from app.routers.security import router as security_router
    SECURITY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import security router: {e}")
    SECURITY_AVAILABLE = False
    security_router = None

if SECURITY_AVAILABLE and "security_router" in globals() and security_router is not None:
    app.include_router(security_router, prefix="/api")
else:
    print("INFO: Security router not registered")

# Encryption router (Pack 18) — optional import
try:
    from app.routers.encryption import router as encryption_router
    ENCRYPTION_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import encryption router: {e}")
    ENCRYPTION_AVAILABLE = False
    encryption_router = None

if ENCRYPTION_AVAILABLE and "encryption_router" in globals() and encryption_router is not None:
    app.include_router(encryption_router, prefix="/api")
else:
    print("INFO: Encryption router not registered")

# Logging router (Pack 19) — optional import
try:
    from app.routers.logging import router as logging_router
    LOGGING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import logging router: {e}")
    LOGGING_AVAILABLE = False
    logging_router = None

if LOGGING_AVAILABLE and "logging_router" in globals() and logging_router is not None:
    app.include_router(logging_router, prefix="/api")
else:
    print("INFO: Logging router not registered")

# Languages router (Pack 21) — optional import
try:
    from app.routers.languages import router as languages_router
    LANGUAGES_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import languages router: {e}")
    LANGUAGES_AVAILABLE = False
    languages_router = None

if LANGUAGES_AVAILABLE and "languages_router" in globals() and languages_router is not None:
    app.include_router(languages_router, prefix="/api")
else:
    print("INFO: Languages router not registered")

# Notifications router (Pack 23) — optional import
try:
    from app.routers.notifications import router as notifications_router
    NOTIFICATIONS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import notifications router: {e}")
    NOTIFICATIONS_AVAILABLE = False
    notifications_router = None

if NOTIFICATIONS_AVAILABLE and "notifications_router" in globals() and notifications_router is not None:
    app.include_router(notifications_router, prefix="/api")
else:
    print("INFO: Notifications router not registered")

# NOTE: Heimdall Build Gate router is now registered unconditionally at app creation (see top of file)# Users router (Pack 24) — optional import
try:
    from app.routers.users import router as users_router
    USERS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import users router: {e}")
    USERS_AVAILABLE = False
    users_router = None

if USERS_AVAILABLE and "users_router" in globals() and users_router is not None:
    app.include_router(users_router, prefix="/api")
else:
    print("INFO: Users router not registered")

# Pack routers (with availability checks)
if GRANTS_AVAILABLE and "grants_router" in globals() and grants_router is not None:
    app.include_router(grants_router, prefix="/api")
else:
    print("WARNING: Grants router not registered")

if BUYERS_AVAILABLE and "buyers_router" in globals() and buyers_router is not None:
    app.include_router(buyers_router, prefix="/api")
else:
    print("WARNING: Buyers router not registered")

if DEALS_AVAILABLE and "deals_router" in globals() and deals_router is not None:
    app.include_router(deals_router, prefix="/api")
else:
    print("WARNING: Deals router not registered")

if MATCH_AVAILABLE and "match_router" in globals() and match_router is not None:
    app.include_router(match_router, prefix="/api")
else:
    print("WARNING: Match router not registered")

if CONTRACTS_AVAILABLE and "contracts_router" in globals() and contracts_router is not None:
    app.include_router(contracts_router, prefix="/api")
else:
    print("WARNING: Contracts router not registered")

if INTAKE_AVAILABLE and "intake_router" in globals() and intake_router is not None:
    app.include_router(intake_router, prefix="/api")
else:
    print("WARNING: Intake router not registered")

if NOTIFY_AVAILABLE and "notify_router" in globals() and notify_router is not None:
    app.include_router(notify_router, prefix="/api")
else:
    print("WARNING: Notify router not registered")

if MESSAGING_AVAILABLE and "messaging_router" in globals() and messaging_router is not None:
    app.include_router(messaging_router, prefix="/api")
else:
    print("INFO: Messaging router not registered")

if PAYMENTS_AVAILABLE and "payments_router" in globals() and payments_router is not None:
    app.include_router(payments_router, prefix="/api")
else:
    print("INFO: Payments router not registered")

if NEGOTIATIONS_AVAILABLE and "negotiations_router" in globals() and negotiations_router is not None:
    app.include_router(negotiations_router, prefix="/api")
else:
    print("INFO: Negotiations router not registered")

if RBAC_AVAILABLE and "rbac_router" in globals() and rbac_router is not None:
    app.include_router(rbac_router, prefix="/api")
else:
    print("INFO: RBAC router not registered")

if INFLUENCE_AVAILABLE and "influence_router" in globals() and influence_router is not None:
    app.include_router(influence_router, prefix="/api")
else:
    print("INFO: Influence router not registered")

if NEGOTIATION_STRATEGIES_AVAILABLE and "negotiation_strategies_router" in globals() and negotiation_strategies_router is not None:
    app.include_router(negotiation_strategies_router, prefix="/api")
else:
    print("INFO: Negotiation Strategies router not registered")

if LEADS_AVAILABLE and "leads_router" in globals() and leads_router is not None:
    app.include_router(leads_router, prefix="/api")
else:
    print("INFO: Leads router not registered")

if ADVANCED_NEGOTIATION_AVAILABLE and "advanced_negotiation_router" in globals() and advanced_negotiation_router is not None:
    app.include_router(advanced_negotiation_router, prefix="/api")
else:
    print("INFO: Advanced Negotiation Techniques router not registered")

if BEHAVIORAL_PROFILING_AVAILABLE and "behavioral_profiling_router" in globals() and behavioral_profiling_router is not None:
    app.include_router(behavioral_profiling_router, prefix="/api")
else:
    print("INFO: Behavioral Profiling router not registered")

if DEAL_ANALYZER_AVAILABLE and "deal_analyzer_router" in globals() and deal_analyzer_router is not None:
    app.include_router(deal_analyzer_router, prefix="/api")
else:
    print("INFO: Deal Analyzer router not registered")

if CLOSERS_AVAILABLE and "closers_router" in globals() and closers_router is not None:
    app.include_router(closers_router, prefix="/api")
else:
    print("INFO: AI Closers router not registered")

if WORKFLOWS_AVAILABLE and "workflows_router" in globals() and workflows_router is not None:
    app.include_router(workflows_router, prefix="/api")
else:
    print("INFO: Workflows router not registered")

if AUDIT_AVAILABLE and "audit_router" in globals() and audit_router is not None:
    app.include_router(audit_router, prefix="/api")
else:
    print("INFO: Audit router not registered")

if FREEZE_AVAILABLE and "freeze_router" in globals() and freeze_router is not None:
    app.include_router(freeze_router, prefix="/api")
else:
    print("INFO: Freeze router not registered")

if KNOWLEDGE_AVAILABLE and "knowledge_router" in globals() and knowledge_router is not None:
    app.include_router(knowledge_router, prefix="/api")
else:
    print("INFO: Knowledge router not registered")

if SCHEDULED_JOBS_AVAILABLE and "scheduled_jobs_router" in globals() and scheduled_jobs_router is not None:
    app.include_router(scheduled_jobs_router, prefix="/api")
else:
    print("INFO: Scheduled Jobs router not registered")

if COMPLIANCE_AVAILABLE and "compliance_router" in globals() and compliance_router is not None:
    app.include_router(compliance_router, prefix="/api")
else:
    print("INFO: Compliance router not registered")

if ORCHESTRATOR_AVAILABLE and "orchestrator_router" in globals() and orchestrator_router is not None:
    app.include_router(orchestrator_router, prefix="/api")
else:
    print("INFO: Orchestrator router not registered")

if FINOPS_AVAILABLE and "finops_router" in globals() and finops_router is not None:
    app.include_router(finops_router, prefix="/api")
else:
    print("INFO: FinOps router not registered")

if ARBITRAGE_AVAILABLE and "arbitrage_router" in globals() and arbitrage_router is not None:
    app.include_router(arbitrage_router, prefix="/api")
else:
    print("INFO: Arbitrage router not registered")

if DOCS_AVAILABLE and "docs_router" in globals() and docs_router is not None:
    app.include_router(docs_router, prefix="/api")
else:
    print("INFO: Docs router not registered")

if POLICIES_AVAILABLE and "policies_router" in globals() and policies_router is not None:
    app.include_router(policies_router, prefix="/api")
else:
    print("INFO: Policies router not registered")

if PROVIDERS_AVAILABLE and "providers_router" in globals() and providers_router is not None:
    app.include_router(providers_router, prefix="/api")
else:
    print("INFO: Providers router not registered")

if BEHAVIOR_AVAILABLE and "behavior_router" in globals() and behavior_router is not None:
    app.include_router(behavior_router, prefix="/api")
else:
    print("INFO: Behavior router not registered")

if BRRRR_AVAILABLE and "brrrr_router" in globals() and brrrr_router is not None:
    app.include_router(brrrr_router, prefix="/api")
else:
    print("INFO: BRRRR router not registered")

if ACCOUNTING_AVAILABLE and "accounting_router" in globals() and accounting_router is not None:
    app.include_router(accounting_router, prefix="/api")
else:
    print("INFO: Accounting router not registered")

if LEGAL_AVAILABLE and "legal_router" in globals() and legal_router is not None:
    app.include_router(legal_router, prefix="/api")
else:
    print("INFO: Legal router not registered")

if NEG_ENHANCE_AVAILABLE and "neg_enhance_router" in globals() and neg_enhance_router is not None:
    app.include_router(neg_enhance_router, prefix="/api")
else:
    print("INFO: Negotiation Enhancer router not registered")

if BLACK_ICE_AVAILABLE and "blackice_router" in globals() and blackice_router is not None:
    app.include_router(blackice_router, prefix="/api")
else:
    print("INFO: Black Ice router not registered")

if CHILDREN_AVAILABLE and "children_router" in globals() and children_router is not None:
    app.include_router(children_router, prefix="/api")
else:
    print("INFO: Children router not registered")

if QUEEN_AVAILABLE and "queen_router" in globals() and queen_router is not None:
    app.include_router(queen_router, prefix="/api")
else:
    print("INFO: Queen router not registered")

if KING_AVAILABLE and "king_router" in globals() and king_router is not None:
    app.include_router(king_router, prefix="/api")
else:
    print("INFO: King router not registered")

if PANTRY_AVAILABLE and "pantry_router" in globals() and pantry_router is not None:
    app.include_router(pantry_router, prefix="/api")
else:
    print("INFO: Pantry router not registered")

if RESORT_AVAILABLE and "resort_router" in globals() and resort_router is not None:
    app.include_router(resort_router, prefix="/api")
else:
    print("INFO: Resort router not registered")

if INTEGRITY_AVAILABLE and "integrity_router" in globals() and integrity_router is not None:
    app.include_router(integrity_router, prefix="/api")
else:
    print("INFO: Integrity router not registered")

if TAX_AVAILABLE and "tax_tracker_router" in globals() and tax_tracker_router is not None:
    app.include_router(tax_tracker_router, prefix="/api")
else:
    print("INFO: Tax Tracker router not registered")

if HEIMDALL_TRAINING_AVAILABLE and "heimdall_training_router" in globals() and heimdall_training_router is not None:
    app.include_router(heimdall_training_router, prefix="/api")
else:
    print("INFO: Heimdall Training router not registered")

if UNDERWRITER_AVAILABLE and "underwriter_router" in globals() and underwriter_router is not None:
    app.include_router(underwriter_router, prefix="/api")
else:
    print("INFO: Underwriter router not registered")

if CLOSER_ENGINE_AVAILABLE and "closer_engine_router" in globals() and closer_engine_router is not None:
    app.include_router(closer_engine_router, prefix="/api")
else:
    print("INFO: Closer Engine router not registered")

if CONTRACT_ENGINE_AVAILABLE and "contract_engine_router" in globals() and contract_engine_router is not None:
    app.include_router(contract_engine_router, prefix="/api")
else:
    print("INFO: Contract Engine router not registered")

if BUYER_MATCH_AVAILABLE and "buyer_match_router" in globals() and buyer_match_router is not None:
    app.include_router(buyer_match_router, prefix="/api")
else:
    print("INFO: Buyer Match router not registered")

# Flow orchestrator routers
if FLOW_LEAD_TO_DEAL_AVAILABLE and "flow_lead_to_deal_router" in globals() and flow_lead_to_deal_router is not None:
    app.include_router(flow_lead_to_deal_router, prefix="/api")
    print("INFO: Flow Lead-to-Deal orchestrator registered")
else:
    print("INFO: Flow Lead-to-Deal orchestrator not registered")

if UNDERWRITING_ENGINE_AVAILABLE and "underwriting_engine_router" in globals() and underwriting_engine_router is not None:
    app.include_router(underwriting_engine_router, prefix="/api")
    print("INFO: Underwriting Engine flow router registered")
else:
    print("INFO: Underwriting Engine flow router not registered")

if FLOW_FULL_PIPELINE_AVAILABLE and "flow_full_pipeline_router" in globals() and flow_full_pipeline_router is not None:
    app.include_router(flow_full_pipeline_router, prefix="/api")
    print("INFO: Full Deal Pipeline orchestrator registered")
else:
    print("INFO: Full Deal Pipeline orchestrator not registered")

if DEAL_WORKFLOW_STATUS_AVAILABLE and "deal_workflow_status_router" in globals() and deal_workflow_status_router is not None:
    app.include_router(deal_workflow_status_router, prefix="/api")
    print("INFO: Deal Workflow Status router registered")
else:
    print("INFO: Deal Workflow Status router not registered")

if FLOW_PREPARE_CLOSING_AVAILABLE and "flow_prepare_closing_router" in globals() and flow_prepare_closing_router is not None:
    app.include_router(flow_prepare_closing_router, prefix="/api")
    print("INFO: Flow Prepare Closing router registered")
else:
    print("INFO: Flow Prepare Closing router not registered")

if CLOSING_PLAYBOOK_AVAILABLE and "closing_playbook_router" in globals() and closing_playbook_router is not None:
    app.include_router(closing_playbook_router, prefix="/api")
    print("INFO: Closing Playbook router registered")
else:
    print("INFO: Closing Playbook router not registered")

if FLOW_NOTIFICATIONS_AVAILABLE and "flow_notifications_router" in globals() and flow_notifications_router is not None:
    app.include_router(flow_notifications_router, prefix="/api")
    print("INFO: Flow Notifications router registered")
else:
    print("INFO: Flow Notifications router not registered")

if FLOW_PROFIT_ALLOCATION_AVAILABLE and "flow_profit_allocation_router" in globals() and flow_profit_allocation_router is not None:
    app.include_router(flow_profit_allocation_router, prefix="/api")
    print("INFO: Flow Profit Allocation router registered")
else:
    print("INFO: Flow Profit Allocation router not registered")

if DEAL_LIFECYCLE_AVAILABLE and "deal_lifecycle_router" in globals() and deal_lifecycle_router is not None:
    app.include_router(deal_lifecycle_router, prefix="/api")
    print("INFO: Deal Lifecycle Orchestrator registered")
else:
    print("INFO: Deal Lifecycle Orchestrator not registered")

if FLOW_FUNFUNDS_PLANNER_AVAILABLE and "flow_funfunds_planner" in globals() and flow_funfunds_planner is not None:
    app.include_router(flow_funfunds_planner.router, prefix="/api")
    print("INFO: FunFunds Planner registered")
else:
    print("INFO: FunFunds Planner not registered")

if BUILDER_AVAILABLE and "builder_router" in globals() and builder_router is not None:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered")
    
if REPORTS_AVAILABLE and "reports_router" in globals() and reports_router is not None:
    app.include_router(reports_router, prefix="/api")
else:
    print("INFO: Reports router not registered (will be available after builder creates it)")
    
if RESEARCH_AVAILABLE:
    if "research_router" in globals() and research_router is not None:
        app.include_router(research_router, prefix="/api")
    if "playbooks_router" in globals() and playbooks_router is not None:
        app.include_router(playbooks_router, prefix="/api")
    if "jobs_router" in globals() and jobs_router is not None:
        app.include_router(jobs_router, prefix="/api")
    if "research_semantic_router" in globals() and research_semantic_router is not None:
        app.include_router(research_semantic_router, prefix="/api")
else:
    print("INFO: Research/Playbooks/Jobs routers not registered")

# Governance Decisions router (PACK R) — optional import
try:
    from app.routers.governance_decisions import router as governance_decisions_router
    GOVERNANCE_DECISIONS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import governance_decisions router: {e}")
    GOVERNANCE_DECISIONS_AVAILABLE = False
    governance_decisions_router = None

if GOVERNANCE_DECISIONS_AVAILABLE and "governance_decisions_router" in globals() and governance_decisions_router is not None:
    app.include_router(governance_decisions_router, prefix="/api")
    print("INFO: Governance Decisions router registered")
else:
    print("INFO: Governance Decisions router not registered")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


@app.get("/debug/routes")
def debug_routes():
    """Debug endpoint to see registered routes and router availability"""
    routes = []
    from fastapi.routing import APIRoute
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {
        "grants_available": GRANTS_AVAILABLE,
        "buyers_available": BUYERS_AVAILABLE,
        "deals_available": DEALS_AVAILABLE,
        "match_available": MATCH_AVAILABLE,
        "contracts_available": CONTRACTS_AVAILABLE,
        "intake_available": INTAKE_AVAILABLE,
        "notify_available": NOTIFY_AVAILABLE,
    "messaging_available": MESSAGING_AVAILABLE,
    "payments_available": PAYMENTS_AVAILABLE,
    "negotiations_available": NEGOTIATIONS_AVAILABLE,
        "rbac_available": RBAC_AVAILABLE,
        "influence_available": INFLUENCE_AVAILABLE,
        "negotiation_strategies_available": NEGOTIATION_STRATEGIES_AVAILABLE,
        "leads_available": LEADS_AVAILABLE,
        "advanced_negotiation_available": ADVANCED_NEGOTIATION_AVAILABLE,
        "behavioral_profiling_available": BEHAVIORAL_PROFILING_AVAILABLE,
        "deal_analyzer_available": DEAL_ANALYZER_AVAILABLE,
    "ai_closers_available": CLOSERS_AVAILABLE,
    "workflows_available": WORKFLOWS_AVAILABLE,
    "audit_available": AUDIT_AVAILABLE,
    "freeze_available": FREEZE_AVAILABLE,
    "knowledge_available": KNOWLEDGE_AVAILABLE,
    "scheduled_jobs_available": SCHEDULED_JOBS_AVAILABLE,
    "compliance_available": COMPLIANCE_AVAILABLE,
    "orchestrator_available": ORCHESTRATOR_AVAILABLE,
    "finops_available": FINOPS_AVAILABLE,
    "arbitrage_available": ARBITRAGE_AVAILABLE,
    "docs_available": DOCS_AVAILABLE,
    "policies_available": POLICIES_AVAILABLE,
    "providers_available": PROVIDERS_AVAILABLE,
    "behavior_available": BEHAVIOR_AVAILABLE,
        "brrrr_available": BRRRR_AVAILABLE,
    "accounting_available": ACCOUNTING_AVAILABLE,
    "legal_available": LEGAL_AVAILABLE,
    "neg_enhance_available": NEG_ENHANCE_AVAILABLE,
    "black_ice_available": BLACK_ICE_AVAILABLE,
    "children_available": CHILDREN_AVAILABLE,
    "king_available": KING_AVAILABLE,
    "pantry_available": PANTRY_AVAILABLE,
    "resort_available": RESORT_AVAILABLE,
    "integrity_available": INTEGRITY_AVAILABLE,
    "tax_available": TAX_AVAILABLE,
    "heimdall_training_available": HEIMDALL_TRAINING_AVAILABLE,
    "underwriter_available": UNDERWRITER_AVAILABLE,
    "closer_engine_available": CLOSER_ENGINE_AVAILABLE,
    "contract_engine_available": CONTRACT_ENGINE_AVAILABLE,
    "buyer_match_available": BUYER_MATCH_AVAILABLE,
        "builder_available": BUILDER_AVAILABLE,
        "reports_available": REPORTS_AVAILABLE,
        "research_available": RESEARCH_AVAILABLE,
        "research_error": RESEARCH_ERROR if 'RESEARCH_ERROR' in globals() else None,
        "total_routes": len(app.routes),
        "routes": routes
    }


# Compatibility health endpoint for tests/runtime expecting /api/health
@app.get("/api/health")
def health():
    return {"ok": True, "app": "Valhalla Backend", "version": "3.4"}

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT
