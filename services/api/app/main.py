"""Main FastAPI application setup."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import engine
from app.models import (
    SelfSupervisionRun, SelfSupervisionFinding,
    CorrectionPlan,
    ExecutionChecklistItem,
    ComplianceEvidence,
    GoLiveState,
)
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables
    Base.metadata.create_all(bind=engine)
    print("[app.main] Database tables created")
    yield
    # Shutdown
    print("[app.main] Shutting down")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Heimdall API",
    description="Self-supervision, drift findings, correction plans, and compliance vault",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PACK CL13: Self-Supervision router
try:
    from app.routers import self_supervision
    app.include_router(self_supervision.router)
    print("[app.main] Self supervision router registered")
except Exception as e:
    print(f"[app.main] Skipping self_supervision router: {e}")

# PACK CL14: Correction Plan router
try:
    from app.routers import correction_plan
    app.include_router(correction_plan.router)
    print("[app.main] Correction plan router registered")
except Exception as e:
    print(f"[app.main] Skipping correction_plan router: {e}")

# PACK CL15: Execution Checklist router
try:
    from app.routers import execution_checklist
    app.include_router(execution_checklist.router)
    print("[app.main] Execution checklist router registered")
except Exception as e:
    print(f"[app.main] Skipping execution_checklist router: {e}")

# PACK CL16: Compliance Evidence router
try:
    from app.routers import compliance_evidence
    app.include_router(compliance_evidence.router)
    print("[app.main] Compliance evidence router registered")
except Exception as e:
    print(f"[app.main] Skipping compliance_evidence router: {e}")

# PACK CL17: Activation Gates router
try:
    from app.routers import activation_gate
    app.include_router(activation_gate.router)
    print("[app.main] Activation gate router registered")
except Exception as e:
    print(f"[app.main] Skipping activation_gate router: {e}")

# PACK CL18: EIA Report Generator router
try:
    from app.routers import eia_report
    app.include_router(eia_report.router)
    print("[app.main] EIA report router registered")
except Exception as e:
    print(f"[app.main] Skipping eia_report router: {e}")

# PACK CL19: Export Endpoints router
try:
    from app.routers import exports
    app.include_router(exports.router)
    print("[app.main] Exports router registered")
except Exception as e:
    print(f"[app.main] Skipping exports router: {e}")

# PACK CL20: System Readiness router
try:
    from app.routers import readiness
    app.include_router(readiness.router)
    print("[app.main] Readiness router registered")
except Exception as e:
    print(f"[app.main] Skipping readiness router: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Heimdall API is running"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
