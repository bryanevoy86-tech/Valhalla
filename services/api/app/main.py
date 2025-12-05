import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import drift, retention

# --- Startup/Shutdown Handler -------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan context manager (replaces deprecated @app.on_event)."""
    # Startup
    if retention.EN:
        async def retention_loop():
            while True:
                await retention.run_once()
                await asyncio.sleep(int(os.getenv("RETENTION_CRON_MINUTES", "30")) * 60)
        asyncio.create_task(retention_loop())
    
    drift.check()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Governance System: Always-on registration --------------------------------
# Register all governance routers to ensure endpoints exist for runtime and tests
from app.routers import governance_king, governance_queen, governance_odin, governance_loki, governance_tyr
from app.routers import governance_orchestrator, heimdall_build_gate, governance_policy

app.include_router(governance_king.router, prefix="/api")
app.include_router(governance_queen.router, prefix="/api")
app.include_router(governance_odin.router, prefix="/api")
app.include_router(governance_loki.router, prefix="/api")
app.include_router(governance_tyr.router, prefix="/api")
app.include_router(governance_orchestrator.router, prefix="/api")
app.include_router(heimdall_build_gate.router)
app.include_router(governance_policy.router, prefix="/api")

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

