import os

def env_flag(name: str, default: str = "0") -> bool:
    """Parse env var as boolean flag."""
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

def phase3_enabled() -> bool:
    """Check if Phase 3 (real data ingestion) is enabled."""
    return os.getenv("VALHALLA_PHASE", "").strip() == "3" and env_flag("VALHALLA_REAL_DATA_INGEST", "0")

def dry_run_enabled() -> bool:
    """Check if DRY-RUN is enabled (must be true in sandbox)."""
    return env_flag("VALHALLA_DRY_RUN", "1")

def outbound_disabled() -> bool:
    """Check if outbound operations are disabled."""
    return env_flag("VALHALLA_DISABLE_OUTBOUND", "1")

def assert_phase3_safety() -> None:
    """
    Phase 3 safety rule: Real data may be ingested ONLY if DRY-RUN is ON and outbound is OFF.
    
    This ensures:
    - Real data goes IN (VALHALLA_REAL_DATA_INGEST=1)
    - No transactions go OUT (VALHALLA_DRY_RUN=1 + VALHALLA_DISABLE_OUTBOUND=1)
    - System remains completely sandboxed
    
    Raises:
        RuntimeError: If Phase 3 is enabled but safety constraints are violated
    """
    if phase3_enabled():
        if not dry_run_enabled():
            raise RuntimeError(
                "PHASE 3 SAFETY VIOLATION: VALHALLA_DRY_RUN must be enabled (=1). "
                "Real data ingestion is only permitted in sandbox mode."
            )
        if not outbound_disabled():
            raise RuntimeError(
                "PHASE 3 SAFETY VIOLATION: Outbound must be disabled (VALHALLA_DISABLE_OUTBOUND=1). "
                "Real data ingestion requires zero outbound operations."
            )
