import os
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import PlainTextResponse

METRICS_ENABLED = os.getenv("METRICS_ENABLED", "false").lower() in ("1", "true", "yes")
NS = os.getenv("METRICS_NAMESPACE", "valhalla")
# Buckets for request latency hist
_bucket_env = os.getenv("METRICS_ROUTE_LAT_BUCKETS", "")
if _bucket_env.strip():
    try:
        ROUTE_BUCKETS = tuple(float(x) for x in _bucket_env.split(","))
    except Exception:
        ROUTE_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)
else:
    ROUTE_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)

_registry = CollectorRegistry()

# --- Web metrics ---
HTTP_REQUESTS = Counter(
    f"{NS}_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=_registry,
)
HTTP_ERRORS = Counter(
    f"{NS}_http_errors_total", "Total HTTP 5xx errors", ["path"], registry=_registry
)
HTTP_LATENCY = Histogram(
    f"{NS}_http_request_duration_seconds",
    "HTTP request latency seconds",
    ["method", "path", "status"],
    buckets=ROUTE_BUCKETS,
    registry=_registry,
)

# --- Job metrics ---
JOB_RUNS = Counter(
    f"{NS}_jobs_runs_total", "Total job runs", ["job_type", "status"], registry=_registry
)
JOB_ACTIVE = Gauge(
    f"{NS}_jobs_active", "Number of active/running jobs", ["job_type"], registry=_registry
)
JOB_LAST_SECONDS = Gauge(
    f"{NS}_job_last_duration_seconds",
    "Last job duration seconds",
    ["job_type", "status"],
    registry=_registry,
)


def _normalize_path(scope_path: str) -> str:
    """
    Simple low-cardinality path normalization.
    Replace numeric IDs with :id and long hex with :hex.
    Adjust as needed for your routing patterns.
    """
    import re

    p = re.sub(r"/\d+", "/:id", scope_path)
    p = re.sub(r"/[0-9a-fA-F]{8,}", "/:hex", p)
    return p


def install_metrics(app: FastAPI):
    if not METRICS_ENABLED:
        return

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = _normalize_path(request.url.path)
        try:
            response: Response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            # count error on uncaught exceptions
            HTTP_ERRORS.labels(path=path).inc()
            HTTP_REQUESTS.labels(method=method, path=path, status="500").inc()
            HTTP_LATENCY.labels(method=method, path=path, status="500").observe(
                time.perf_counter() - start
            )
            raise
        else:
            HTTP_REQUESTS.labels(method=method, path=path, status=status).inc()
            HTTP_LATENCY.labels(method=method, path=path, status=status).observe(
                time.perf_counter() - start
            )
            if status.startswith("5"):
                HTTP_ERRORS.labels(path=path).inc()
        return response

    @app.get("/admin/metrics", include_in_schema=False)
    async def metrics_endpoint():
        data = generate_latest(_registry)
        return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)


# --- Helpers for workers/jobs ---
class JobTimer:
    """
    Usage:
        with JobTimer("export"):
            ... do the work ...
    """

    def __init__(self, job_type: str):
        self.job_type = job_type
        self._t0 = None

    def __enter__(self):
        self._t0 = time.perf_counter()
        JOB_ACTIVE.labels(job_type=self.job_type).inc()
        return self

    def __exit__(self, exc_type, exc, tb):
        dur = time.perf_counter() - self._t0
        status = "ERROR" if exc else "OK"
        JOB_RUNS.labels(job_type=self.job_type, status=status).inc()
        JOB_LAST_SECONDS.labels(job_type=self.job_type, status=status).set(dur)
        JOB_ACTIVE.labels(job_type=self.job_type).dec()
        # do not suppress exceptions
        return False


def job_timer(job_type: str):
    """Decorator for async/sync job functions."""

    def deco(fn):
        import functools
        import inspect

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def aw(*a, **kw):
                with JobTimer(job_type):
                    return await fn(*a, **kw)

            return aw
        else:

            @functools.wraps(fn)
            def w(*a, **kw):
                with JobTimer(job_type):
                    return fn(*a, **kw)

            return w

    return deco
