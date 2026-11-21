"""Truthful critical FastAPI router registration status.

The app can remain alive for diagnostics, but readiness must be RED when a
mandatory router fails to import or is absent. We never treat number of other
loaded routers as proof of required capabilities.
"""
from __future__ import annotations

REQUIRED_ROUTER_NAMES = frozenset({
    "jarvis",                 # private owner conversation and inbox
    "go_live",                # owner release and emergency control
    "system_self_check",      # private operational integrity inspection
    "system_status",          # protected metadata, not release evidence
    "loki_worker",            # authenticated independent reviewer interface
    "loki",                   # separate independent audit boundary
    "auth_weweb",             # owner/user identity
    "completion_registry",   # Phase Three, governance and legacy orchestration
    "product_artifacts",        # owner-attested internal asset staging
    "legacy_playbooks",       # internal clone and mirror rehearsals
    "prime_business_factory", # durable owned execution lane
    "norns_forecasts",          # timestamped observable forecasts
    "prime_specialist_schedules",  # durable owner-authorized shadow cadence
    "builder",                # controlled software building
    "marketing",              # marketing registry
    "media_engine",           # content records
    "saas_access",            # subordinate subscription access
    "governance_king",        # original valuation/mission evaluator
    "governance_queen",       # sustainability/owner wellbeing evaluator
    "governance_odin",        # market and strategic focus evaluator
    "governance_loki",        # adverse-case risk evaluator
    "governance_tyr",         # legal/ethics hard-stop evaluator
    "governance_orchestrator",# combined five-god decision interface
})


def compute_router_integrity(
    loaded_names: set[str],
    import_failures: dict[str, str] | None = None,
) -> dict:
    import_failures = import_failures or {}
    loaded = set(loaded_names)
    missing = sorted(REQUIRED_ROUTER_NAMES - loaded)
    failures = {
        name: str(reason)
        for name, reason in sorted(import_failures.items())
        if name in REQUIRED_ROUTER_NAMES
    }
    return {
        "ready": not missing and not failures,
        "required_count": len(REQUIRED_ROUTER_NAMES),
        "loaded_count": len(REQUIRED_ROUTER_NAMES & loaded),
        "missing": missing,
        "import_failures": failures,
    }
