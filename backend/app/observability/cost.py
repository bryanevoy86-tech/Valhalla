import os

from .metrics import NS, Counter, _registry

EN = os.getenv("COST_ENABLED", "false").lower() in ("1", "true", "yes")

BYTES_S3 = Counter(
    f"{NS}_cost_s3_egress_bytes_total", "S3 egress bytes", ["bucket"], registry=_registry
)
TOKENS_AI = Counter(
    f"{NS}_cost_ai_tokens_total", "AI tokens", ["model", "kind"], registry=_registry
)
SECONDS_JOB = Counter(
    f"{NS}_cost_job_seconds_total", "Compute seconds", ["job_type"], registry=_registry
)


def add_s3(bucket: str, bytes_out: int):
    if EN:
        BYTES_S3.labels(bucket=bucket).inc(bytes_out)


def add_tokens(model: str, kind: str, tokens: int):
    if EN:
        TOKENS_AI.labels(model=model, kind=kind).inc(tokens)


def add_job_seconds(job_type: str, seconds: float):
    if EN:
        SECONDS_JOB.labels(job_type=job_type).inc(seconds)
