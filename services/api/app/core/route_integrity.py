"""Truthful critical FastAPI router registration status.

The app can remain alive for diagnostics, but readiness must be RED when a
mandatory router fails to import or is absent. We never treat number of other
loaded routers as proof of required capabilities.
"""
from __future__ import annotations

REQUIRED_ROUTER_NAMES = frozenset({
    "auth_weweb",             # owner/user identity
    "completion_registry",   # Phase Three, governance and legacy orchestration
    "prime_business_factory", # durable owned execution lane
    "builder",                # controlled software building
    "marketing",              # marketing registry
    "media_engine",           # content records
    "saas_access",            # subordinate subscription access
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
