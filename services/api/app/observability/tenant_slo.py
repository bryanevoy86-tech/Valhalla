import os

from .metrics import NS, Counter, _registry

EN = os.getenv("TENANT_SLO_ENABLED", "false").lower() in ("1", "true", "yes")

SLO_ERR = Counter(
    f"{NS}_tenant_http_errors_total", "Tenant HTTP errors", ["tenant"], registry=_registry
)
SLO_OK = Counter(f"{NS}_tenant_http_ok_total", "Tenant HTTP ok", ["tenant"], registry=_registry)


def record(tenant: str, code: int):
    if not EN:
        return
    if 200 <= code < 500:
        SLO_OK.labels(tenant=tenant).inc()
    else:
        SLO_ERR.labels(tenant=tenant).inc()
