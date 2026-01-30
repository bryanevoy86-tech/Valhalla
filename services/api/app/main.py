import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.observability import drift, retention
from app.core.db import verify_schema_initialized

log = logging.getLogger("valhalla.startup")

# --- Startup/Shutdown Handler -------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan context manager (replaces deprecated @app.on_event)."""
    # Startup
    
    # Verify schema is initialized (migrations applied)
    try:
        verify_schema_initialized()
    except RuntimeError as e:
        log.error("Schema validation failed: %s", e)
        raise
    
    if retention.EN:
        async def retention_loop():
            while True:
                await retention.run_once()
                await asyncio.sleep(int(os.getenv("RETENTION_CRON_MINUTES", "30")) * 60)
        asyncio.create_task(retention_loop())
    
    # Drift check with controlled kill switch
    try:
        run_drift = os.getenv("DRIFT_CHECK_ON_STARTUP", "1").lower() in {"1", "true", "yes", "on"}
        if run_drift:
            log.info("Running drift.check() on startup (DRIFT_CHECK_ON_STARTUP=1)")
            drift.check()
        else:
            log.warning("Skipping drift.check() on startup (DRIFT_CHECK_ON_STARTUP=0)")
    except Exception as e:
        # IMPORTANT: do not suppress. Log full details then crash hard.
        log.exception("Startup failed during drift.check(): %s", e)
        raise
    
    yield
    # Shutdown (if needed later)


# --- Core FastAPI app ---------------------------------------------------------

app = FastAPI(
    title="Valhalla API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

# ✅ HARD BYPASS: OPTIONS always returns 200 (runs FIRST, before all other middleware)
@app.middleware("http")
async def allow_options_preflight(request: Request, call_next):
    """
    Browser CORS preflight fix: OPTIONS requests always return 200.
    This decorator-based middleware runs FIRST, before any other middleware
    can reject it (auth, validation, etc).
    """
    if request.method == "OPTIONS":
        return Response(status_code=200)
    return await call_next(request)

# ✅ CORS Middleware: Allow WeWeb and explicit header handling
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://editor.weweb.io",
        "https://app.weweb.io",
        "https://valhalla.weweb-preview.io",
        "https://preview.weweb.io",
        # Optional: add your published WeWeb domain when ready
        # "https://yourapp.weweb.app",
        # Allow localhost for dev
        "http://localhost:3000",
        "http://localhost:4000",
        "http://localhost:8000",
    ],
    allow_credentials=False,  # IMPORTANT: keep False unless you are using cookies with credentials
    allow_methods=["*"],      # includes OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,            # 24 hours for preflight cache
)

# --- DEBUG: Route List Endpoint (remove after debugging) ----------------------
from fastapi.responses import JSONResponse

@app.get("/__routes", include_in_schema=False)
def __routes():
    return sorted({r.path for r in app.router.routes})

# --- PACK TW: Correlation ID Middleware (must be early) ----------------------
from app.core.correlation_middleware import CorrelationIdMiddleware
app.add_middleware(CorrelationIdMiddleware)

# --- PACK TU: Global Error Handling (must be early) --------------------------
from app.core.error_handling import register_error_handlers
register_error_handlers(app)

# --- Go-Live & Kill-Switch Enforcement (Prime Law Safeguard) ----------------
from app.core.go_live_middleware import GoLiveMiddleware
app.add_middleware(GoLiveMiddleware)

# --- Execution Classification Enforcement (Precise Go-Live Governance) -------
from app.core.execution_class_middleware import ExecutionClassMiddleware
app.add_middleware(ExecutionClassMiddleware)

# --- Governance System: Always-on registration --------------------------------
# Register all governance routers to ensure endpoints exist for runtime and tests
from app.routers import governance_king, governance_queen, governance_odin, governance_loki, governance_tyr
from app.routers import governance_orchestrator, heimdall_build_gate, governance_policy
from app.routers import go_live as governance_go_live
from app.routers import risk as governance_risk
from app.routers import heimdall_governance as governance_heimdall
from app.routers import regression as governance_regression
from app.routers import runbook as governance_runbook
from app.routers import market_policy as governance_market_policy
from app.routers import followup_ladder as followups_ladder
from app.routers import buyer_liquidity as buyers_liquidity
from app.routers import offer_strategy as deals_offer_strategy

# --- Core Engine Governance (PACK 1-5: Canonical enforcement) ----------------
from app.routers import engine_admin
from app.routers import runbook_status

app.include_router(governance_king.router, prefix="/api")
app.include_router(governance_queen.router, prefix="/api")
app.include_router(governance_odin.router, prefix="/api")
app.include_router(governance_loki.router, prefix="/api")
app.include_router(governance_tyr.router, prefix="/api")
app.include_router(governance_orchestrator.router, prefix="/api")
app.include_router(heimdall_build_gate.router)
app.include_router(governance_policy.router, prefix="/api")
app.include_router(governance_go_live.router, prefix="/api")
app.include_router(governance_risk.router, prefix="/api")
app.include_router(governance_heimdall.router, prefix="/api")
app.include_router(governance_regression.router, prefix="/api")
app.include_router(governance_runbook.router, prefix="/api")

# DEBUG: Print all governance/runbook routes
_governance_routes = [r.path for r in app.router.routes if "governance" in r.path or "runbook" in r.path]
print(f"DEBUG: Registered governance/runbook routes: {_governance_routes}")

app.include_router(governance_market_policy.router, prefix="/api")
app.include_router(followups_ladder.router, prefix="/api")
app.include_router(buyers_liquidity.router, prefix="/api")
app.include_router(deals_offer_strategy.router, prefix="/api")

# --- Core Engine Governance Routers (canonical enforcement) --
app.include_router(engine_admin.router)
# ISOLATED: Commenting out runbook_status.router to isolate governance_runbook router
# app.include_router(runbook_status.router)

# --- PACK H: Professional Behavioral Signal Extraction -------------------------
# Safe behavioral analysis from public data sources (no psychology, no diagnosis)
try:
    from app.routers import pro_behavioral_extract
    app.include_router(pro_behavioral_extract.router)
except Exception as e:
    print("WARNING: Could not load pro_behavioral_extract:", e)

# --- PACK I: Professional Alignment Engine ----------------------------------------
# Compares behavioral signals to Valhalla's ideal profile for operational compatibility
try:
    from app.routers import pro_alignment_engine
    app.include_router(pro_alignment_engine.router)
except Exception as e:
    print("WARNING: pro_alignment_engine failed:", e)

# --- PACK J: Professional Scorecard Engine ----------------------------------------
# Tracks ongoing performance of lawyers, accountants, VAs, contractors (operational only)
try:
    from app.routers import pro_scorecard
    app.include_router(pro_scorecard.router)
except Exception as e:
    print("WARNING: pro_scorecard load failed:", e)

# --- PACK K: Retainer Lifecycle Engine --------------------------------------------
# Manages retainer agreements, tracks hours, costs, renewals, and consumption
try:
    from app.routers import pro_retainer
    app.include_router(pro_retainer.router)
except Exception as e:
    print("WARNING: pro_retainer load failed:", e)

# --- PACK L: Professional Handoff Engine ------------------------------------------
# Generates escalation packets with professional details, scorecards, and deal context
try:
    from app.routers import pro_handoff
    app.include_router(pro_handoff.router)
except Exception as e:
    print("WARNING: pro_handoff load failed:", e)

# --- PACK M: Professional Task Lifecycle Engine ------------------------------------
# Links tasks to professionals for tracking what's waiting on which human
try:
    from app.routers import pro_tasks
    app.include_router(pro_tasks.router)
except Exception as e:
    print("WARNING: pro_tasks load failed:", e)

# --- PACK N: Contract Lifecycle Engine ---------------------------------------------
# Tracks contract status from draft through review, approval, signature, and archival
try:
    from app.routers import contracts_lifecycle
    app.include_router(contracts_lifecycle.router)
except Exception as e:
    print("WARNING: contracts_lifecycle load failed:", e)

# --- PACK O: Document Routing Engine -----------------------------------------------
# Tracks document delivery to professionals with sent/opened/acknowledged status
try:
    from app.routers import document_routing
    app.include_router(document_routing.router)
except Exception as e:
    print("WARNING: document_routing load failed:", e)

# --- PACK P: Deal Finalization Engine ----------------------------------------------
# Validates all requirements met and marks deals as finalized when ready
try:
    from app.routers import deal_finalization
    app.include_router(deal_finalization.router)
except Exception as e:
    print("WARNING: deal_finalization load failed:", e)

# --- PACK Q: Internal Auditor -------------------------------------------------------
# Scans deals/workflows for missing steps, logs compliance/process issues
try:
    from app.routers import internal_auditor
    app.include_router(internal_auditor.router)
except Exception as e:
    print("WARNING: internal_auditor load failed:", e)

# --- PACK R: Governance Integration -------------------------------------------------
# Records governance decisions (approve/deny/override) by roles with audit trail
try:
    from app.routers import governance_decisions
    app.include_router(governance_decisions.router)
except Exception as e:
    print("WARNING: governance_decisions load failed:", e)

# --- PACK SP: Life Event & Crisis Management Engine ----------------------------
# Organizes crisis response plans, tracks events, and manages operational readiness
try:
    from app.routers.pack_sp_sq_so import router_sp
    app.include_router(router_sp)
except Exception as e:
    print("WARNING: pack_sp (crisis management) load failed:", e)

# --- PACK SQ: Partner / Marriage Stability Ops Module ---------------------------
# Practical life logistics for shared responsibilities and household operations
try:
    from app.routers.pack_sp_sq_so import router_sq
    app.include_router(router_sq)
except Exception as e:
    print("WARNING: pack_sq (partner/marriage ops) load failed:", e)

# --- PACK SO: Long-Term Legacy & Succession Archive Engine ----------------------
# Captures legacy, inheritance, knowledge transfer, and multi-stage succession
try:
    from app.routers.pack_sp_sq_so import router_so
    app.include_router(router_so)
except Exception as e:
    print("WARNING: pack_so (legacy/succession) load failed:", e)

# --- PACK ST: Financial Stress Early Warning Engine ---------------------------
# User-defined financial threshold monitoring with stress event tracking
try:
    from app.routers.pack_st_su_sv import router_st
    app.include_router(router_st)
except Exception as e:
    print("WARNING: pack_st (financial stress) load failed:", e)

# --- PACK SU: Personal Safety & Risk Mitigation Planner -------------------------
# User-defined safety routines, checklists, contingency plans (no judgment)
try:
    from app.routers.pack_st_su_sv import router_su
    app.include_router(router_su)
except Exception as e:
    print("WARNING: pack_su (personal safety) load failed:", e)

# --- PACK SV: Empire Growth Navigator -------------------------------------------
# Goal hierarchy (Goal→Milestone→Action) with progress tracking (0-100%)
try:
    from app.routers.pack_st_su_sv import router_sv
    app.include_router(router_sv)
except Exception as e:
    print("WARNING: pack_sv (empire growth) load failed:", e)

# --- PACK SW: Life Timeline & Major Milestones Engine ---------------------------
# Complete life story chronology with events, milestones, and timeline snapshots
try:
    from app.routers.pack_sw_sx_sy import router_sw
    app.include_router(router_sw)
except Exception as e:
    print("WARNING: pack_sw (life timeline) load failed:", e)

# --- PACK SX: Emotional Neutrality & Stability Log ----------------------------
# User-stated emotional/logistical states without interpretation or diagnosis
try:
    from app.routers.pack_sw_sx_sy import router_sx
    app.include_router(router_sx)
except Exception as e:
    print("WARNING: pack_sx (emotional stability) load failed:", e)

# --- PACK SY: Strategic Decision History & Reason Archive ----------------------
# Complete decision archive with revisions, reasoning, and strategy chains
try:
    from app.routers.pack_sw_sx_sy import router_sy
    app.include_router(router_sy)
except Exception as e:
    print("WARNING: pack_sy (strategic decisions) load failed:", e)

# --- PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive -----------------
# Philosophy records, empire principles, and philosophy snapshots
try:
    from app.routers.pack_sz_ta_tb import router_sz
    app.include_router(router_sz)
except Exception as e:
    print("WARNING: pack_sz (core philosophy) load failed:", e)

# --- PACK TA: Trust, Loyalty & Relationship Mapping (Safe, Non-Psychological) ---
# Relationship profiles, trust event logs, and relationship map snapshots
try:
    from app.routers.pack_sz_ta_tb import router_ta
    app.include_router(router_ta)
except Exception as e:
    print("WARNING: pack_ta (relationships & trust) load failed:", e)

# --- PACK TB: Daily Behavioral Rhythm & Tempo Engine ----------------------------
# Daily rhythm profiles, tempo rules, and daily tempo snapshots
try:
    from app.routers.pack_sz_ta_tb import router_tb
    app.include_router(router_tb)
except Exception as e:
    print("WARNING: pack_tb (daily rhythm & tempo) load failed:", e)

# --- PACK TC: Heimdall Ultra Mode Engine -------------------------------------------
# Operational configuration for Ultra execution mode (initiative, escalation, scanning)
try:
    from app.routes.heimdall_ultra import router as heimdall_ultra_router
    app.include_router(heimdall_ultra_router)
except Exception as e:
    print("WARNING: pack_tc (heimdall ultra mode) load failed:", e)

# --- PACK TD: Resilience & Recovery Planner -------------------------------------------
# Track setbacks, recovery plans, and recovery actions for resilience building
try:
    from app.routes.resilience import router as resilience_router
    app.include_router(resilience_router)
except Exception as e:
    print("WARNING: pack_td (resilience & recovery) load failed:", e)

# --- PACK TE: Life Roles & Capacity Engine -----------------------------------------
# Track life roles (Father, Builder, Operator) and capacity load per role
try:
    from app.routes.life_roles import router as life_roles_router
    app.include_router(life_roles_router)
except Exception as e:
    print("WARNING: pack_te (life roles & capacity) load failed:", e)

# --- PACK TF: System Tune List Engine -----------------------------------------------
# Master checklist of system areas and improvement items with status tracking
try:
    from app.routes.system_tune import router as system_tune_router
    app.include_router(system_tune_router)
except Exception as e:
    print("WARNING: pack_tf (system tune list) load failed:", e)

# --- PACK TG: Mental Load Offloading Engine ----------------------------------------------
# Brain-dump entries and daily mental load summaries
try:
    from app.routes.mental_load_tg import router as mental_load_router
    app.include_router(mental_load_router)
except Exception as e:
    print("WARNING: pack_tg (mental load offloading) load failed:", e)

# --- PACK TH: Crisis Management Engine -----------------------------------------------
# Crisis profiles, action steps, and event logging
try:
    from app.routes.crisis import router as crisis_router
    app.include_router(crisis_router)
except Exception as e:
    print("WARNING: pack_th (crisis management) load failed:", e)

# --- PACK TI: Financial Stress Early Warning Engine --------------------------------
# Threshold indicators and stress event tracking
try:
    from app.routes.financial_stress import router as financial_stress_router
    app.include_router(financial_stress_router)
except Exception as e:
    print("WARNING: pack_ti (financial stress early warning) load failed:", e)


# --- System endpoints: root + health -----------------------------------------

@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint – Heimdall status + welcome message.
    """
    return {
        "message": "Welcome to Valhalla Legacy API",
        "status": "Heimdall Operational",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
async def health():
    """
    Simple health check for uptime monitors and Render.
    """
    return {"status": "ok", "heimdall": "online"}


@app.get("/healthz", tags=["System"])
async def healthz():
    """
    Secondary health endpoint (some scripts/tools use /healthz).
    """
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"service": "valhalla-api", "version": "1.0.0"}


@app.get("/api/features")
def features():
    return [{"id": 1, "name": "valhalla"}]


# --- API v1 router (optional, but safe) --------------------------------------

try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping /api/v1 router: {e}")

try:
    from app.routers.loki import router as loki_router
    app.include_router(loki_router)
except Exception as e:
    print(f"[app.main] Skipping loki router: {e}")

try:
    from app.routers.god_cases import router as god_cases_router
    app.include_router(god_cases_router)
except Exception as e:
    print(f"[app.main] Skipping god_cases router: {e}")

try:
    from app.routers.sync_engine import router as sync_engine_router
    app.include_router(sync_engine_router)
except Exception as e:
    print(f"[app.main] Skipping sync_engine router: {e}")

try:
    from app.routers.specialists import router as specialists_router
    app.include_router(specialists_router)
except Exception as e:
    print(f"[app.main] Skipping specialists router: {e}")

try:
    from app.routers.lawyer_feed import router as lawyer_feed_router
    app.include_router(lawyer_feed_router)
except Exception as e:
    print(f"[app.main] Skipping lawyer_feed router: {e}")

try:
    from app.routers.tax_bridge import router as tax_bridge_router
    app.include_router(tax_bridge_router)
except Exception as e:
    print(f"[app.main] Skipping tax_bridge router: {e}")

try:
    from app.routers.god_verdicts import router as god_verdicts_router
    app.include_router(god_verdicts_router)
except Exception as e:
    print(f"[app.main] Skipping god_verdicts router: {e}")

try:
    from app.routers.disputes import router as disputes_router
    app.include_router(disputes_router)
except Exception as e:
    print(f"[app.main] Skipping disputes router: {e}")

try:
    from app.routers.god_arbitration import router as god_arbitration_router
    app.include_router(god_arbitration_router)
except Exception as e:
    print(f"[app.main] Skipping god_arbitration router: {e}")

try:
    from app.routers.specialist_feedback import router as specialist_feedback_router
    app.include_router(specialist_feedback_router)
except Exception as e:
    print(f"[app.main] Skipping specialist_feedback router: {e}")

try:
    from app.api.v1.backup import router as backup_router
    app.include_router(backup_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping backup router: {e}")

try:
    from app.api.v1.security import router as security_router
    app.include_router(security_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping security router: {e}")

try:
    from app.api.v1.optimization import router as optimization_router
    app.include_router(optimization_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping optimization router: {e}")

try:
    from app.api.v1.telemetry import router as telemetry_router
    app.include_router(telemetry_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping telemetry router: {e}")

try:
    from app.api.v1.diagnostics import router as diagnostics_router
    app.include_router(diagnostics_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping diagnostics router: {e}")

try:
    from app.api.v1.bus import router as bus_router
    app.include_router(bus_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping bus router: {e}")

try:
    from app.api.v1.arbitration import router as arbitration_router
    app.include_router(arbitration_router, prefix="/api/v1")
except Exception as e:
    print(f"[app.main] Skipping arbitration router: {e}")

try:
    from app.api.api_v1.endpoints.staff import router as staff_router
    app.include_router(staff_router, prefix="/api/v1/staff", tags=["Staff"])
except Exception as e:
    print(f"[app.main] Skipping staff router: {e}")

try:
    from app.api.api_v1.endpoints.contractors import router as contractors_router
    app.include_router(contractors_router, prefix="/api/v1/contractors", tags=["Contractors"])
except Exception as e:
    print(f"[app.main] Skipping contractors router: {e}")

try:
    from app.api.api_v1.endpoints.resort import router as resort_router
    app.include_router(resort_router, prefix="/api/v1/resort", tags=["Resort"])
except Exception as e:
    print(f"[app.main] Skipping resort router: {e}")

try:
    from app.api.api_v1.endpoints.trust import router as trust_router
    app.include_router(trust_router, prefix="/api/v1/trust", tags=["Trust"])
except Exception as e:
    print(f"[app.main] Skipping trust router: {e}")

try:
    from app.api.api_v1.endpoints.legacy import router as legacy_router
    app.include_router(legacy_router, prefix="/api/v1/legacy", tags=["Legacy"])
except Exception as e:
    print(f"[app.main] Skipping legacy router: {e}")

try:
    from app.api.api_v1.endpoints.shield import router as shield_router
    app.include_router(shield_router, prefix="/api/v1/shield", tags=["Shield Mode"])
except Exception as e:
    print(f"[app.main] Skipping shield router: {e}")

# FunFunds Planner flow router
try:
    from app.routers import flow_funfunds_planner
    app.include_router(flow_funfunds_planner.router, prefix="/api")
    print("[app.main] FunFunds Planner router registered")
except Exception as e:
    print(f"[app.main] Skipping funfunds_planner router: {e}")

# FunFunds Presets flow router (lean/growth modes)
try:
    from app.routers import flow_funfunds_presets
    app.include_router(flow_funfunds_presets.router, prefix="/api")
    print("[app.main] FunFunds Presets router registered")
except Exception as e:
    print(f"[app.main] Skipping funfunds_presets router: {e}")

# Tax Snapshot flow router (CRA-style tax breakdown)
try:
    from app.routers import flow_tax_snapshot
    app.include_router(flow_tax_snapshot.router, prefix="/api")
    print("[app.main] Tax Snapshot router registered")
except Exception as e:
    print(f"[app.main] Skipping tax_snapshot router: {e}")

# Governance-gated flow router
try:
    from app.routers import flow_governance_gate
    app.include_router(flow_governance_gate.router, prefix="/api")
    print("[app.main] Governance-Gated Flow router registered")
except Exception as e:
    print(f"[app.main] Skipping flow_governance_gate router: {e}")

# Portfolio Dashboard router (deal summary and snapshots)
try:
    from app.routers import portfolio_dashboard
    app.include_router(portfolio_dashboard.router, prefix="/api")
    print("[app.main] Portfolio Dashboard router registered")
except Exception as e:
    print(f"[app.main] Skipping portfolio_dashboard router: {e}")

# Governance King router
try:
    from app.routers import governance_king
    app.include_router(governance_king.router, prefix="/api")
    print("[app.main] Governance King router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_king router: {e}")

# Governance Queen router
try:
    from app.routers import governance_queen
    app.include_router(governance_queen.router, prefix="/api")
    print("[app.main] Governance Queen router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_queen router: {e}")

# Governance Odin router
try:
    from app.routers import governance_odin
    app.include_router(governance_odin.router, prefix="/api")
    print("[app.main] Governance Odin router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_odin router: {e}")

# Governance Loki router
try:
    from app.routers import governance_loki
    app.include_router(governance_loki.router, prefix="/api")
    print("[app.main] Governance Loki router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_loki router: {e}")

# Governance Tyr router
try:
    from app.routers import governance_tyr
    app.include_router(governance_tyr.router, prefix="/api")
    print("[app.main] Governance Tyr router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_tyr router: {e}")

# Governance Orchestrator router (calls all five gods)
try:
    from app.routers import governance_orchestrator
    app.include_router(governance_orchestrator.router, prefix="/api")
    print("[app.main] Governance Orchestrator router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_orchestrator router: {e}")

# PACK W: System Status router (system metadata and completion status)
try:
    from app.routers import system_status
    app.include_router(system_status.router)
    print("[app.main] System status router registered")
except Exception as e:
    print(f"[app.main] Skipping system_status router: {e}")

# PACK X: Wholesaling Engine router (lead → offer → contract → assignment → closed pipeline)
try:
    from app.routers import wholesale_engine
    app.include_router(wholesale_engine.router)
    print("[app.main] Wholesaling engine router registered")
except Exception as e:
    print(f"[app.main] Skipping wholesale_engine router: {e}")

# PACK Y: Disposition Engine router (buyers, assignments, dispo outcomes)
try:
    from app.routers import dispo_engine
    app.include_router(dispo_engine.router)
    print("[app.main] Disposition engine router registered")
except Exception as e:
    print(f"[app.main] Skipping dispo_engine router: {e}")

# PACK Z: Global Holdings Engine router (empire view: properties, resorts, trusts, etc.)
try:
    from app.routers import holdings_engine
    app.include_router(holdings_engine.router)
    print("[app.main] Holdings engine router registered")
except Exception as e:
    print(f"[app.main] Skipping holdings_engine router: {e}")

# PACK AA: Story Engine router (story templates, episodes, mood/purpose tagging)
try:
    from app.routers import story_engine
    app.include_router(story_engine.router)
    print("[app.main] Story engine router registered")
except Exception as e:
    print(f"[app.main] Skipping story_engine router: {e}")

# PACK AB: Education Engine router (courses, lessons, enrollments, progress tracking)
try:
    from app.routers import education_engine
    app.include_router(education_engine.router)
    print("[app.main] Education engine router registered")
except Exception as e:
    print(f"[app.main] Skipping education_engine router: {e}")

# PACK AC: Media Engine router (content, channels, publish logs, distribution)
try:
    from app.routers import media_engine
    app.include_router(media_engine.router)
    print("[app.main] Media engine router registered")
except Exception as e:
    print(f"[app.main] Skipping media_engine router: {e}")

# PACK AD: SaaS Access Engine router (plans, subscriptions, module access control)
try:
    from app.routers import saas_access
    app.include_router(saas_access.router)
    print("[app.main] SaaS access engine router registered")
except Exception as e:
    print(f"[app.main] Skipping saas_access router: {e}")

# PACK AE: Public Investor Module router (profiles, project summaries, read-only)
try:
    from app.routers import investor_module
    app.include_router(investor_module.router)
    print("[app.main] Investor module router registered")
except Exception as e:
    print(f"[app.main] Skipping investor_module router: {e}")

# PACK AF: Unified Empire Dashboard router (read-only aggregation of all engines)
try:
    from app.routers import empire_dashboard
    app.include_router(empire_dashboard.router)
    print("[app.main] Empire dashboard router registered")
except Exception as e:
    print(f"[app.main] Skipping empire_dashboard router: {e}")

# PACK AG: Notification Orchestrator router (channels, templates, sending, logs)
try:
    from app.routers import notification_orchestrator
    app.include_router(notification_orchestrator.router)
    print("[app.main] Notification orchestrator router registered")
except Exception as e:
    print(f"[app.main] Skipping notification_orchestrator router: {e}")

# PACK AH: Event Log / Timeline Engine router (universal event logging)
try:
    from app.routers import event_log
    app.include_router(event_log.router)
    print("[app.main] Event log router registered")
except Exception as e:
    print(f"[app.main] Skipping event_log router: {e}")

# PACK AI: Scenario Simulator router (scenarios and simulation runs)
try:
    from app.routers import scenario_simulator
    app.include_router(scenario_simulator.router)
    print("[app.main] Scenario simulator router registered")
except Exception as e:
    print(f"[app.main] Skipping scenario_simulator router: {e}")

# PACK AJ: Notification Bridge router (event-to-notification dispatch with user preferences)
try:
    from app.routers import notification_bridge
    app.include_router(notification_bridge.router)
    print("[app.main] Notification bridge router registered")
except Exception as e:
    print(f"[app.main] Skipping notification_bridge router: {e}")

# PACK AK: Analytics / Metrics Engine router (read-only empire metrics aggregation)
try:
    from app.routers import analytics_engine
    app.include_router(analytics_engine.router)
    print("[app.main] Analytics engine router registered")
except Exception as e:
    print(f"[app.main] Skipping analytics_engine router: {e}")

# PACK AL: Brain State Snapshot Engine router (system state snapshots for Heimdall)
try:
    from app.routers import brain_state
    app.include_router(brain_state.router)
    print("[app.main] Brain state snapshot router registered")
except Exception as e:
    print(f"[app.main] Skipping brain_state router: {e}")

# PACK AM: Data Lineage Engine router (audit trail of all entity changes)
try:
    from app.routers import data_lineage
    app.include_router(data_lineage.router)
    print("[app.main] Data lineage router registered")
except Exception as e:
    print(f"[app.main] Skipping data_lineage router: {e}")

# PACK AN: Auto-Heal & Integrity Monitor router (system integrity checks)
try:
    from app.routers import integrity_monitor
    app.include_router(integrity_monitor.router)
    print("[app.main] Integrity monitor router registered")
except Exception as e:
    print(f"[app.main] Skipping integrity_monitor router: {e}")

# PACK AO: Explainability Engine router (human-readable explanations for decisions)
try:
    from app.routers import explanation_engine
    app.include_router(explanation_engine.router)
    print("[app.main] Explanation engine router registered")
except Exception as e:
    print(f"[app.main] Skipping explanation_engine router: {e}")

# PACK AP: Decision Governance Engine router (policy-based decision framework)
try:
    from app.routers import decision_governance
    app.include_router(decision_governance.router)
    print("[app.main] Decision governance router registered")
except Exception as e:
    print(f"[app.main] Skipping decision_governance router: {e}")

# PACK AQ: Workflow Guardrails router (role-based permission system with violation logging)
try:
    from app.routers import workflow_guardrails
    app.include_router(workflow_guardrails.router)
    print("[app.main] Workflow guardrails router registered")
except Exception as e:
    print(f"[app.main] Skipping workflow_guardrails router: {e}")

# PACK AR: Heimdall Workload Balancer router (job queue management and workload control)
try:
    from app.routers import heimdall_workload
    app.include_router(heimdall_workload.router)
    print("[app.main] Heimdall workload router registered")
except Exception as e:
    print(f"[app.main] Skipping heimdall_workload router: {e}")

# PACK AS: Empire Journal Engine router (master journal with notes, insights, lessons)
try:
    from app.routers import empire_journal
    app.include_router(empire_journal.router)
    print("[app.main] Empire journal router registered")
except Exception as e:
    print(f"[app.main] Skipping empire_journal router: {e}")

# PACK AT: User-Facing Summary Snapshot router (plain language summaries for family/ops)
try:
    from app.routers import user_summary
    app.include_router(user_summary.router)
    print("[app.main] User summary router registered")
except Exception as e:
    print(f"[app.main] Skipping user_summary router: {e}")

# PACK AU: Trust & Residency Profile router (operational trust and jurisdiction tracking)
try:
    from app.routers import trust_residency
    app.include_router(trust_residency.router)
    print("[app.main] Trust residency router registered")
except Exception as e:
    print(f"[app.main] Skipping trust_residency router: {e}")

# PACK AV: Narrative Story Mode router (story prompts and generated outputs)
try:
    from app.routers import story_mode
    app.include_router(story_mode.router)
    print("[app.main] Story mode router registered")
except Exception as e:
    print(f"[app.main] Skipping story_mode router: {e}")

# PACK AW: Crosslink / Relationship Graph router (unified entity relationship mapping)
try:
    from app.routers import entity_links
    app.include_router(entity_links.router)
    print("[app.main] Entity links router registered")
except Exception as e:
    print(f"[app.main] Skipping entity_links router: {e}")

# PACK AX: Feature Flags & Experiments router (safe feature rollout and A/B testing)
try:
    from app.routers import feature_flags
    app.include_router(feature_flags.router)
    print("[app.main] Feature flags router registered")
except Exception as e:
    print(f"[app.main] Skipping feature_flags router: {e}")

# PACK SA: Grant Eligibility Engine router (strategic framework for grant organization)
try:
    from app.routers import grant_eligibility
    app.include_router(grant_eligibility.router)
    print("[app.main] Grant eligibility router registered")
except Exception as e:
    print(f"[app.main] Skipping grant_eligibility router: {e}")

# PACK SB: Business Registration Navigator router (non-legal workflow for business registration)
try:
    from app.routers import registration_navigator
    app.include_router(registration_navigator.router)
    print("[app.main] Registration navigator router registered")
except Exception as e:
    print(f"[app.main] Skipping registration_navigator router: {e}")

# PACK SC: Banking Structure Planner router (safe organizational mapping for account structure)
try:
    from app.routers import banking_structure_planner
    app.include_router(banking_structure_planner.router)
    print("[app.main] Banking structure planner router registered")
except Exception as e:
    print(f"[app.main] Skipping banking_structure_planner router: {e}")

# PACK SD: Credit Card & Spending Framework router (compliance checking, non-directive)
try:
    from app.routers import credit_card_spending
    app.include_router(credit_card_spending.router)
    print("[app.main] Credit card spending router registered")
except Exception as e:
    print(f"[app.main] Skipping credit_card_spending router: {e}")

# PACK SE: Vehicle Use & Expense Categorization router (CRA-compliant recordkeeping)
try:
    from app.routers import vehicle_tracking
    app.include_router(vehicle_tracking.router)
    print("[app.main] Vehicle tracking router registered")
except Exception as e:
    print(f"[app.main] Skipping vehicle_tracking router: {e}")

# PACK SF: CRA Document Vault & Organization router (pure data organization, no tax determination)
try:
    from app.routers import cra_organization
    app.include_router(cra_organization.router)
    print("[app.main] CRA organization router registered")
except Exception as e:
    print(f"[app.main] Skipping cra_organization router: {e}")

# PACK SG: Income Routing & Separation Engine router (user-defined allocation rules, neutral execution)
try:
    from app.routers import income_routing
    app.include_router(income_routing.router)
    print("[app.main] Income routing router registered")
except Exception as e:
    print(f"[app.main] Skipping income_routing router: {e}")

# PACK SH: Multi-Year Projection Snapshot Framework router (user-driven scenarios, no automatic forecasting)
try:
    from app.routers import projection_framework
    app.include_router(projection_framework.router)
    print("[app.main] Projection framework router registered")
except Exception as e:
    print(f"[app.main] Skipping projection_framework router: {e}")

# PACK SI: Real Estate Acquisition & BRRRR Planner router (deal tracking, reno, refinance, cashflow)
try:
    from app.routers import brrrr_planner
    app.include_router(brrrr_planner.router)
    print("[app.main] BRRRR planner router registered")
except Exception as e:
    print(f"[app.main] Skipping brrrr_planner router: {e}")

# PACK SJ: Wholesale Deal Machine router (deal pipeline, offers, assignments, non-advisory)
try:
    from app.routers import wholesale_deals
    app.include_router(wholesale_deals.router)
    print("[app.main] Wholesale deals router registered")
except Exception as e:
    print(f"[app.main] Skipping wholesale_deals router: {e}")

# PACK SK: Arbitrage/Side-Hustle Opportunity Tracker router (user-scored opportunities, performance tracking)
try:
    from app.routers import opportunity_tracker
    app.include_router(opportunity_tracker.router)
    print("[app.main] Opportunity tracker router registered")
except Exception as e:
    print(f"[app.main] Skipping opportunity_tracker router: {e}")

# PACK SL: Personal Master Dashboard router (life operations, routines, goals, family, mood)
try:
    from app.routers import personal_dashboard
    app.include_router(personal_dashboard.router)
    print("[app.main] Personal dashboard router registered")
except Exception as e:
    print(f"[app.main] Skipping personal_dashboard router: {e}")

# PACK SM: Kids Education & Development Engine router (learning plans, education logs)
try:
    from app.routers import kids_education
    app.include_router(kids_education.router)
    print("[app.main] Kids education router registered")
except Exception as e:
    print(f"[app.main] Skipping kids_education router: {e}")

# PACK SN: Mental Load Offloading Engine router (brain dump, task management)
try:
    from app.routers import mental_load
    app.include_router(mental_load.router)
    print("[app.main] Mental load router registered")
except Exception as e:
    print(f"[app.main] Skipping mental_load router: {e}")

# PACK SO: Long-Term Empire Governance Map router (roles, hierarchy, succession)
try:
    from app.routers import empire_governance
    app.include_router(empire_governance.router)
    print("[app.main] Empire governance router registered")
except Exception as e:
    print(f"[app.main] Skipping empire_governance router: {e}")

# PACK TQ: Security Policy & Blocklist Engine router (Tyr-owned policy management)
try:
    from app.routers import security_policy
    app.include_router(security_policy.router)
    print("[app.main] Security policy router registered")
except Exception as e:
    print(f"[app.main] Skipping security_policy router: {e}")

# PACK TR: Security Action Workflow router (requests, approvals, execution)
try:
    from app.routers import security_actions
    app.include_router(security_actions.router)
    print("[app.main] Security actions router registered")
except Exception as e:
    print(f"[app.main] Skipping security_actions router: {e}")

# PACK TS: Honeypot Registry & Telemetry Bridge router (decoy instances, event logging)
try:
    from app.routers import honeypot_bridge
    app.include_router(honeypot_bridge.router)
    print("[app.main] Honeypot bridge router registered")
except Exception as e:
    print(f"[app.main] Skipping honeypot_bridge router: {e}")

# PACK TT: Security Dashboard Aggregator router (unified security view)
try:
    from app.routers import security_dashboard
    app.include_router(security_dashboard.router)
    print("[app.main] Security dashboard router registered")
except Exception as e:
    print(f"[app.main] Skipping security_dashboard router: {e}")

# PACK TV: System Log & Audit Trail router (structured logging)
try:
    from app.routers import system_log
    app.include_router(system_log.router)
    print("[app.main] System log router registered")
except Exception as e:
    print(f"[app.main] Skipping system_log router: {e}")

# PACK TX: System Health, Readiness & Metrics router (Kubernetes probes)
# Note: system_health router is already imported and integrated above
# This ensures the new endpoints (/live, /ready, /metrics) are available

# PACK L0-06: Telemetry & Observability router (event ingestion and tracing)
try:
    from app.routers import telemetry_event
    app.include_router(telemetry_event.router)
    print("[app.main] Telemetry event router registered")
except Exception as e:
    print(f"[app.main] Skipping telemetry_event router: {e}")

# PACK L0-08: Scheduled Jobs & Task Queue router (job lifecycle management)
try:
    from app.routers import job
    app.include_router(job.router)
    print("[app.main] Job router registered")
except Exception as e:
    print(f"[app.main] Skipping job router: {e}")

# PACK L0-08: Scheduled Jobs router (legacy router, if different from job)
try:
    from app.routers import scheduled_jobs
    app.include_router(scheduled_jobs.router)
    print("[app.main] Scheduled jobs router registered")
except Exception as e:
    print(f"[app.main] Skipping scheduled_jobs router: {e}")

# PACK L0-09: Strategic Decision Engine routers
# Strategic Mode (operational modes)
try:
    from app.routers import strategic_mode
    app.include_router(strategic_mode.router)
    print("[app.main] Strategic mode router registered")
except Exception as e:
    print(f"[app.main] Skipping strategic_mode router: {e}")

# Strategic Event (event recording and timeline)
try:
    from app.routers import strategic_event
    app.include_router(strategic_event.router)
    print("[app.main] Strategic event router registered")
except Exception as e:
    print(f"[app.main] Skipping strategic_event router: {e}")

# Strategic Decision (proposal and approval workflow)
try:
    from app.routers import strategic_decision
    app.include_router(strategic_decision.router)
    print("[app.main] Strategic decision router registered")
except Exception as e:
    print(f"[app.main] Skipping strategic_decision router: {e}")

# Trajectory (long-term planning and projection)
try:
    from app.routers import trajectory
    app.include_router(trajectory.router)
    print("[app.main] Trajectory router registered")
except Exception as e:
    print(f"[app.main] Skipping trajectory router: {e}")

# Tuning Rules (decision thresholds)
try:
    from app.routers import tuning_rules
    app.include_router(tuning_rules.router)
    print("[app.main] Tuning rules router registered")
except Exception as e:
    print(f"[app.main] Skipping tuning_rules router: {e}")

# Workflow Guardrails (safety constraints)
try:
    from app.routers import workflow_guardrails
    app.include_router(workflow_guardrails.router)
    print("[app.main] Workflow guardrails router registered")
except Exception as e:
    print(f"[app.main] Skipping workflow_guardrails router: {e}")

# PACK TY: Route Index & Debug Explorer router (enumerate all mounted routes)
try:
    from app.routers import route_index
    app.include_router(route_index.router)
    print("[app.main] Route index router registered")
except Exception as e:
    print(f"[app.main] Skipping route_index router: {e}")

# PACK TZ: Config & Environment Registry router (non-secret configuration management)
try:
    from app.routers import system_config
    app.include_router(system_config.router)
    print("[app.main] System config router registered")
except Exception as e:
    print(f"[app.main] Skipping system_config router: {e}")

# PACK UA: Feature Flag Engine router (toggle features on/off, safe experiments)
try:
    from app.routers import feature_flags
    app.include_router(feature_flags.router)
    print("[app.main] Feature flags router registered")
except Exception as e:
    print(f"[app.main] Skipping feature_flags router: {e}")

# PACK UB: Deployment Profile & Smoke Test Runner router (deployment info + health checks)
try:
    from app.routers import deployment_profile
    app.include_router(deployment_profile.router)
    print("[app.main] Deployment profile router registered")
except Exception as e:
    print(f"[app.main] Skipping deployment_profile router: {e}")

# PACK UC: Rate Limiting & Quota Engine router (per-IP/user/key rate limits)
try:
    from app.routers import rate_limit
    app.include_router(rate_limit.router)
    print("[app.main] Rate limit router registered")
except Exception as e:
    print(f"[app.main] Skipping rate_limit router: {e}")

# PACK UD: API Key & Client Registry router (client registration and key management)
try:
    from app.routers import api_clients
    app.include_router(api_clients.router)
    print("[app.main] API clients router registered")
except Exception as e:
    print(f"[app.main] Skipping api_clients router: {e}")

# PACK UE: Maintenance Window & Freeze Switch router (maintenance mode and windows)
try:
    from app.routers import maintenance
    app.include_router(maintenance.router)
    print("[app.main] Maintenance router registered")
except Exception as e:
    print(f"[app.main] Skipping maintenance router: {e}")

# PACK UF: Admin Ops Console router (high-level admin control plane)
try:
    from app.routers import admin_ops
    app.include_router(admin_ops.router)
    print("[app.main] Admin ops router registered")
except Exception as e:
    print(f"[app.main] Skipping admin_ops router: {e}")

# PACK UG: Notification & Alert Channel Engine router (channels, outbox, delivery)
try:
    from app.routers import notification_channel
    app.include_router(notification_channel.router)
    print("[app.main] Notification channel router registered")
except Exception as e:
    print(f"[app.main] Skipping notification_channel router: {e}")

# PACK UH: Export & Snapshot Job Engine router (export jobs, status tracking)
try:
    from app.routers import export_job
    app.include_router(export_job.router)
    print("[app.main] Export job router registered")
except Exception as e:
    print(f"[app.main] Skipping export_job router: {e}")

# PACK UI: Data Retention Policy Registry router (retention configuration)
try:
    from app.routers import data_retention
    app.include_router(data_retention.router)
    print("[app.main] Data retention router registered")
except Exception as e:
    print(f"[app.main] Skipping data_retention router: {e}")

# PACK UJ: Read-Only Shield Middleware (blocks writes during maintenance/read-only mode)
# Must be added BEFORE error handlers in middleware stack
try:
    from app.core.read_only_middleware import ReadOnlyShieldMiddleware
    app.add_middleware(ReadOnlyShieldMiddleware)
    print("[app.main] Read-only shield middleware registered")
except Exception as e:
    print(f"[app.main] Skipping read_only_shield middleware: {e}")

# PACK CI1: Decision Recommendation Engine router
try:
    from app.routers import decision_recommendation
    app.include_router(decision_recommendation.router)
    print("[app.main] Decision recommendation router registered")
except Exception as e:
    print(f"[app.main] Skipping decision_recommendation router: {e}")

# PACK CI2: Opportunity Engine router
try:
    from app.routers import opportunity
    app.include_router(opportunity.router)
    print("[app.main] Opportunity router registered")
except Exception as e:
    print(f"[app.main] Skipping opportunity router: {e}")

# PACK CI3: Trajectory Engine router
try:
    from app.routers import trajectory
    app.include_router(trajectory.router)
    print("[app.main] Trajectory router registered")
except Exception as e:
    print(f"[app.main] Skipping trajectory router: {e}")

# PACK CI4: Insight Synthesizer router
try:
    from app.routers import insight
    app.include_router(insight.router)
    print("[app.main] Insight router registered")
except Exception as e:
    print(f"[app.main] Skipping insight router: {e}")

# PACK CI5: Heimdall Tuning Ruleset Engine router
try:
    from app.routers import tuning_rules
    app.include_router(tuning_rules.router)
    print("[app.main] Tuning rules router registered")
except Exception as e:
    print(f"[app.main] Skipping tuning_rules router: {e}")

# PACK CI6: Trigger & Threshold Engine router
try:
    from app.routers import triggers
    app.include_router(triggers.router)
    print("[app.main] Triggers router registered")
except Exception as e:
    print(f"[app.main] Skipping triggers router: {e}")

# PACK CI7: Strategic Mode Engine router
try:
    from app.routers import strategic_mode
    app.include_router(strategic_mode.router)
    print("[app.main] Strategic mode router registered")
except Exception as e:
    print(f"[app.main] Skipping strategic_mode router: {e}")

# PACK CI8: Narrative / Chapter Engine router
try:
    from app.routers import narrative
    app.include_router(narrative.router)
    print("[app.main] Narrative router registered")
except Exception as e:
    print(f"[app.main] Skipping narrative router: {e}")

# PACK CL9-10: Decision Outcome Log & Feedback API router
try:
    from app.routers import decision_outcome
    app.include_router(decision_outcome.router)
    print("[app.main] Decision outcome router registered")
except Exception as e:
    print(f"[app.main] Skipping decision_outcome router: {e}")

# PACK CL11: Strategic Memory Timeline router
try:
    from app.routers import strategic_event
    app.include_router(strategic_event.router)
    print("[app.main] Strategic event router registered")
except Exception as e:
    print(f"[app.main] Skipping strategic_event router: {e}")

# PACK CL12: Model Provider Registry router
try:
    from app.routers import model_provider
    app.include_router(model_provider.router)
    print("[app.main] Model provider router registered")
except Exception as e:
    print(f"[app.main] Skipping model_provider router: {e}")

# PACK 60: System Finalization & CI/CD Hardening router
try:
    from app.routes import system_finalization
    app.include_router(system_finalization.router)
    print("[app.main] System finalization router registered")
except Exception as e:
    print(f"[app.main] Skipping system_finalization router: {e}")

# PACK 61: Prime Directive Engine router
try:
    from app.routes import prime_directive
    app.include_router(prime_directive.router)
    print("[app.main] Prime directive router registered")
except Exception as e:
    print(f"[app.main] Skipping prime_directive router: {e}")

# PACK 62: Capital Allocation Engine router
try:
    from app.routes import capital_allocation
    app.include_router(capital_allocation.router)
    print("[app.main] Capital allocation router registered")
except Exception as e:
    print(f"[app.main] Skipping capital_allocation router: {e}")

# PACK 63: Evolution Engine router
try:
    from app.routes import evolution
    app.include_router(evolution.router)
    print("[app.main] Evolution router registered")
except Exception as e:
    print(f"[app.main] Skipping evolution router: {e}")

# PACK 64: Contract Engine Finalization router
try:
    from app.routes import contract_finalization
    app.include_router(contract_finalization.router)
    print("[app.main] Contract finalization router registered")
except Exception as e:
    print(f"[app.main] Skipping contract_finalization router: {e}")

# PACK 65: Clone Engine router
try:
    from app.routes import clone_engine
    app.include_router(clone_engine.router)
    print("[app.main] Clone engine router registered")
except Exception as e:
    print(f"[app.main] Skipping clone_engine router: {e}")

# PACK 66: System Release router
try:
    from app.routes import system_release
    app.include_router(system_release.router)
    print("[app.main] System release router registered")
except Exception as e:
    print(f"[app.main] Skipping system_release router: {e}")

# PACK 67: Story Video Engine router
try:
    from app.routes import story_video
    app.include_router(story_video.router)
    print("[app.main] Story video router registered")
except Exception as e:
    print(f"[app.main] Skipping story_video router: {e}")

# PACK 68: Blueprint Generator router
try:
    from app.routes import blueprint
    app.include_router(blueprint.router)
    print("[app.main] Blueprint router registered")
except Exception as e:
    print(f"[app.main] Skipping blueprint router: {e}")

# PACK 69: Code Compliance router
try:
    from app.routes import code_compliance
    app.include_router(code_compliance.router)
    print("[app.main] Code compliance router registered")
except Exception as e:
    print(f"[app.main] Skipping code_compliance router: {e}")

# PACK 70: Contractor Packet router
try:
    from app.routes import contractor_packet
    app.include_router(contractor_packet.router)
    print("[app.main] Contractor packet router registered")
except Exception as e:
    print(f"[app.main] Skipping contractor_packet router: {e}")

# PACK 71: Reno Cost Simulator router
try:
    from app.routes import reno_cost_sim
    app.include_router(reno_cost_sim.router)
    print("[app.main] Reno cost sim router registered")
except Exception as e:
    print(f"[app.main] Skipping reno_cost_sim router: {e}")

# PACK 72: BRRRR & Permit router
try:
    from app.routes import brrrr_permit
    app.include_router(brrrr_permit.router)
    print("[app.main] BRRRR & permit router registered")
except Exception as e:
    print(f"[app.main] Skipping brrrr_permit router: {e}")

# PACK 73: Alerts & SLA router
try:
    from app.routes import alerts
    app.include_router(alerts.router)
    print("[app.main] Alerts router registered")
except Exception as e:
    print(f"[app.main] Skipping alerts router: {e}")

# PACK 74: Data IO router
try:
    from app.routes import data_io
    app.include_router(data_io.router)
    print("[app.main] Data IO router registered")
except Exception as e:
    print(f"[app.main] Skipping data_io router: {e}")

# PACK 75: Integrity & Telemetry router
try:
    from app.routes import integrity_telemetry
    app.include_router(integrity_telemetry.router)
    print("[app.main] Integrity & telemetry router registered")
except Exception as e:
    print(f"[app.main] Skipping integrity_telemetry router: {e}")

# PACK 76: Protection Stack router
try:
    from app.routes import protection_stack
    app.include_router(protection_stack.router)
    print("[app.main] Protection stack router registered")
except Exception as e:
    print(f"[app.main] Skipping protection_stack router: {e}")

# PACK 77: Education Org router
try:
    from app.routes import education_org
    app.include_router(education_org.router)
    print("[app.main] Education org router registered")
except Exception as e:
    print(f"[app.main] Skipping education_org router: {e}")

# PACK 78: Education Student router
try:
    from app.routes import education_student
    app.include_router(education_student.router)
    print("[app.main] Education student router registered")
except Exception as e:
    print(f"[app.main] Skipping education_student router: {e}")

# PACK 79: Curriculum Builder router
try:
    from app.routes import curriculum_builder
    app.include_router(curriculum_builder.router)
    print("[app.main] Curriculum builder router registered")
except Exception as e:
    print(f"[app.main] Skipping curriculum_builder router: {e}")

# PACK 80: Education Assessment router
try:
    from app.routes import education_assessment
    app.include_router(education_assessment.router)
    print("[app.main] Education assessment router registered")
except Exception as e:
    print(f"[app.main] Skipping education_assessment router: {e}")

# PACK 81: Industry Registry router
try:
    from app.routes import industry_registry
    app.include_router(industry_registry.router)
    print("[app.main] Industry registry router registered")
except Exception as e:
    print(f"[app.main] Skipping industry_registry router: {e}")

# PACK 82: Product Line router
try:
    from app.routes import product_line
    app.include_router(product_line.router)
    print("[app.main] Product line router registered")
except Exception as e:
    print(f"[app.main] Skipping product_line router: {e}")

# PACK 83: Cost Model router
try:
    from app.routes import cost_model
    app.include_router(cost_model.router)
    print("[app.main] Cost model router registered")
except Exception as e:
    print(f"[app.main] Skipping cost_model router: {e}")

# PACK 84: Industry Revenue Simulator router
try:
    from app.routes import industry_revenue
    app.include_router(industry_revenue.router)
    print("[app.main] Industry revenue simulator router registered")
except Exception as e:
    print(f"[app.main] Skipping industry_revenue router: {e}")

# PACK 85: Industry Regulation router
try:
    from app.routes import industry_regulation
    app.include_router(industry_regulation.router)
    print("[app.main] Industry regulation router registered")
except Exception as e:
    print(f"[app.main] Skipping industry_regulation router: {e}")

# PACK 86: Narrative Documentary router
try:
    from app.routes import narrative_record
    app.include_router(narrative_record.router)
    print("[app.main] Narrative documentary router registered")
except Exception as e:
    print(f"[app.main] Skipping narrative_record router: {e}")

# PACK 87: Marketing Automation router
try:
    from app.routes import marketing
    app.include_router(marketing.router)
    print("[app.main] Marketing automation router registered")
except Exception as e:
    print(f"[app.main] Skipping marketing router: {e}")

# PACK 88: Employee/VA Training Engine router
try:
    from app.routes import training
    app.include_router(training.router)
    print("[app.main] Training engine router registered")
except Exception as e:
    print(f"[app.main] Skipping training router: {e}")

# PACK 89: Household OS router
try:
    from app.routes import household
    app.include_router(household.router)
    print("[app.main] Household OS router registered")
except Exception as e:
    print(f"[app.main] Skipping household router: {e}")

# PACK 90: Health & Fitness Engine router
try:
    from app.routes import health
    app.include_router(health.router)
    print("[app.main] Health & fitness engine router registered")
except Exception as e:
    print(f"[app.main] Skipping health router: {e}")

# PACK 91: Legal Drafting Engine router
try:
    from app.routes import legal_drafting
    app.include_router(legal_drafting.router)
    print("[app.main] Legal drafting engine router registered")
except Exception as e:
    print(f"[app.main] Skipping legal_drafting router: {e}")

# PACK 92: HR Engine router
try:
    from app.routes import hr
    app.include_router(hr.router)
    print("[app.main] HR engine router registered")
except Exception as e:
    print(f"[app.main] Skipping hr router: {e}")

# PACK 93: Multi-Zone Expansion router
try:
    from app.routes import zone
    app.include_router(zone.router)
    print("[app.main] Multi-zone expansion router registered")
except Exception as e:
    print(f"[app.main] Skipping zone router: {e}")

# PACK 94: Zone Replication router
try:
    from app.routes import zone_clone
    app.include_router(zone_clone.router)
    print("[app.main] Zone replication router registered")
except Exception as e:
    print(f"[app.main] Skipping zone_clone router: {e}")

# PACK 95: Expansion Risk & Compliance router
try:
    from app.routes import expansion_risk
    app.include_router(expansion_risk.router)
    print("[app.main] Expansion risk & compliance router registered")
except Exception as e:
    print(f"[app.main] Skipping expansion_risk router: {e}")

# PACK-CORE-PRELAUNCH-01: Alerts Engine router
try:
    from app.core.prelaunch.alerts_engine.router import router as alerts_router
    app.include_router(alerts_router)
    print("[app.main] Alerts engine router registered")
except Exception as e:
    print(f"[app.main] Skipping alerts_engine router: {e}")

# PACK-CORE-PRELAUNCH-01: Daily Ops router
try:
    from app.core.prelaunch.daily_ops.router import router as daily_ops_router
    app.include_router(daily_ops_router)
    print("[app.main] Daily ops router registered")
except Exception as e:
    print(f"[app.main] Skipping daily_ops router: {e}")

# PACK-CORE-PRELAUNCH-01: Scenarios Engine router
try:
    from app.core.prelaunch.scenarios_engine.router import router as scenarios_router
    app.include_router(scenarios_router)
    print("[app.main] Scenarios engine router registered")
except Exception as e:
    print(f"[app.main] Skipping scenarios_engine router: {e}")

# PACK-CORE-PRELAUNCH-01: Unified Log router
try:
    from app.core.prelaunch.unified_log.router import router as events_router
    app.include_router(events_router)
    print("[app.main] Unified log router registered")
except Exception as e:
    print(f"[app.main] Skipping unified_log router: {e}")

# PACK-CORE-PRELAUNCH-01: Safeguard Matrix router
try:
    from app.core.prelaunch.safeguard_matrix.router import router as safeguards_router
    app.include_router(safeguards_router)
    print("[app.main] Safeguard matrix router registered")
except Exception as e:
    print(f"[app.main] Skipping safeguard_matrix router: {e}")

# PACK-CORE-PRELAUNCH-01: Preference Engine router
try:
    from app.core.prelaunch.preference_engine.router import router as prefs_router
    app.include_router(prefs_router)
    print("[app.main] Preference engine router registered")
except Exception as e:
    print(f"[app.main] Skipping preference_engine router: {e}")

# PACK-CORE-PRELAUNCH-01: Automations Core router
try:
    from app.core.prelaunch.automations_core.router import router as automations_router
    app.include_router(automations_router)
    print("[app.main] Automations core router registered")
except Exception as e:
    print(f"[app.main] Skipping automations_core router: {e}")

# PACK-CORE-PRELAUNCH-01: Bootloader router
try:
    from app.core.prelaunch.bootloader.router import router as bootloader_router
    app.include_router(bootloader_router)
    print("[app.main] Bootloader router registered")
except Exception as e:
    print(f"[app.main] Skipping bootloader router: {e}")

# PACK-PRELAUNCH-09: Behavior Engine router
try:
    from app.core.prelaunch.behavior_engine.router import router as behavior_router
    app.include_router(behavior_router)
    print("[app.main] Behavior engine router registered")
except Exception as e:
    print(f"[app.main] Skipping behavior_engine router: {e}")

# PACK-PRELAUNCH-10: EIA Guardian router
try:
    from app.core.prelaunch.eia_guardian.router import router as eia_router
    app.include_router(eia_router)
    print("[app.main] EIA guardian router registered")
except Exception as e:
    print(f"[app.main] Skipping eia_guardian router: {e}")

# PACK-PRELAUNCH-11: Arbitrage Guard router
try:
    from app.core.prelaunch.arbitrage_guard.router import router as arbitrage_router
    app.include_router(arbitrage_router)
    print("[app.main] Arbitrage guard router registered")
except Exception as e:
    print(f"[app.main] Skipping arbitrage_guard router: {e}")

# PACK-PRELAUNCH-12: BRRRR Stability router
try:
    from app.core.prelaunch.brrrr_stability.router import router as brrrr_router
    app.include_router(brrrr_router)
    print("[app.main] BRRRR stability router registered")
except Exception as e:
    print(f"[app.main] Skipping brrrr_stability router: {e}")

# Zone Expansion Engine router
try:
    from app.core.prelaunch.zone_expansion.router import router as zone_expansion_router
    app.include_router(zone_expansion_router)
    print("[app.main] Zone expansion router registered")
except Exception as e:
    print(f"[app.main] Skipping zone_expansion router: {e}")

# Kids Safe Browser router
try:
    from app.core.prelaunch.safe_browser.router import router as safe_browser_router
    app.include_router(safe_browser_router)
    print("[app.main] Safe browser router registered")
except Exception as e:
    print(f"[app.main] Skipping safe_browser router: {e}")

# Story Admin router
try:
    from app.core.prelaunch.story_admin.router import router as story_admin_router
    app.include_router(story_admin_router)
    print("[app.main] Story admin router registered")
except Exception as e:
    print(f"[app.main] Skipping story_admin router: {e}")

# System Health Endpoint router
try:
    from app.core.prelaunch.health_endpoint.router import router as health_endpoint_router
    app.include_router(health_endpoint_router)
    print("[app.main] Health endpoint router registered")
except Exception as e:
    print(f"[app.main] Skipping health_endpoint router: {e}")

# Negotiation Engine router (FREYJA)
try:
    from app.core.prelaunch.negotiation_engine.router import router as negotiation_engine_router
    app.include_router(negotiation_engine_router)
    print("[app.main] Negotiation engine router registered")
except Exception as e:
    print(f"[app.main] Skipping negotiation_engine router: {e}")

# Trajectory Engine router
try:
    from app.core.prelaunch.trajectory_engine.router import router as trajectory_engine_router
    app.include_router(trajectory_engine_router)
    print("[app.main] Trajectory engine router registered")
except Exception as e:
    print(f"[app.main] Skipping trajectory_engine router: {e}")

# SaaS Manager router
try:
    from app.core.prelaunch.saas_manager.router import router as saas_manager_router
    app.include_router(saas_manager_router)
    print("[app.main] SaaS manager router registered")
except Exception as e:
    print(f"[app.main] Skipping saas_manager router: {e}")

# Governance Engine router
try:
    from app.core.prelaunch.governance_engine.router import router as governance_engine_router
    app.include_router(governance_engine_router)
    print("[app.main] Governance engine router registered")
except Exception as e:
    print(f"[app.main] Skipping governance_engine router: {e}")

# Family OS router
try:
    from app.core.prelaunch.family_os.router import router as family_os_router
    app.include_router(family_os_router)
    print("[app.main] Family OS router registered")
except Exception as e:
    print(f"[app.main] Skipping family_os router: {e}")

# Kids Hub router
try:
    from app.core.prelaunch.kids_hub.router import router as kids_hub_router
    app.include_router(kids_hub_router)
    print("[app.main] Kids Hub router registered")
except Exception as e:
    print(f"[app.main] Skipping kids_hub router: {e}")

# Negotiation Memory router
try:
    from app.core.prelaunch.negotiation_memory.router import router as negotiation_memory_router
    app.include_router(negotiation_memory_router)
    print("[app.main] Negotiation memory router registered")
except Exception as e:
    print(f"[app.main] Skipping negotiation_memory router: {e}")

# Contract Engine Upgrade router
try:
    from app.core.prelaunch.contract_engine_upgrade.router import router as contract_upgrade_router
    app.include_router(contract_upgrade_router)
    print("[app.main] Contract engine upgrade router registered")
except Exception as e:
    print(f"[app.main] Skipping contract_engine_upgrade router: {e}")






