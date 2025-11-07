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

# Auto-create tables on startup (dev-friendly; safe if tables already exist)
try:
    from app.core.db import Base, engine
    @app.on_event("startup")
    def startup_create_tables():
        try:
            Base.metadata.create_all(bind=engine)
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

# Users router (Pack 24) — optional import
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
