import json
import os
import time
import uuid
from typing import Dict

from fastapi import Request
from opentelemetry import trace
from starlette.types import ASGIApp, Receive, Scope, Send

from .logging import request_id_ctx, route_id_ctx, user_id_ctx
from .scrub import scrub_headers, scrub_json_text_maybe

ENABLED = os.getenv("REPLAY_ENABLED", "false").lower() in ("1", "true", "yes")
JSON_PATH = os.getenv("REPLAY_JSON_PATH", "./replay.jsonl")
MAX_KB = int(os.getenv("REPLAY_MAX_BODY_KB", "256"))
CAPTURE_CODES = {
    int(x.strip())
    for x in os.getenv("REPLAY_CAPTURE_STATUSES", "500,502,503,504").split(",")
    if x.strip()
}
SENSITIVE = {
    h.strip().lower()
    for h in os.getenv("REPLAY_SENSITIVE_HEADERS", "authorization,cookie,set-cookie").split(",")
}
DEFAULT_DEST = os.getenv("REPLAY_DEFAULT_DEST", "http://localhost:8000")
ALLOW_HOSTS = {
    h.strip().lower()
    for h in os.getenv("REPLAY_ALLOW_DEST_HOSTS", "localhost,127.0.0.1").split(",")
}
TIMEOUT = int(os.getenv("REPLAY_TIMEOUT_SECS", "20"))

os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)


def _otel_ids():
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if not ctx or not ctx.is_valid:
        return None, None
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")


def _sanitize_headers(h: Dict[str, str]) -> Dict[str, str]:
    out = {}
    for k, v in h.items():
        if k.lower() in SENSITIVE:
            continue
        out[k] = v
    return out


async def _read_body_limited(request: Request) -> bytes:
    body = await request.body()
    if len(body) > MAX_KB * 1024:
        return body[: MAX_KB * 1024]
    return body


class ReplayCaptureMiddleware:
    """
    Captures requests whose RESPONSE status is in CAPTURE_CODES.
    Writes one JSON object per line to REPLAY_JSON_PATH.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if not ENABLED or scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)
        body_bytes = b""
        # read body early (so we can write it if failing). Starlette buffers it for downstream.
        try:
            body_bytes = await _read_body_limited(request)
        except Exception:
            body_bytes = b""

        status_holder = {"code": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)

        start_ms = int(time.time() * 1000)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            code = status_holder["code"]
            if code and code in CAPTURE_CODES:
                # Context
                trace_id, span_id = _otel_ids()
                rid = request_id_ctx.get()
                route = route_id_ctx.get() or scope.get("path", "")
                uid = user_id_ctx.get()

                item = {
                    "id": uuid.uuid4().hex,
                    "@timestamp": start_ms,
                    "method": request.method,
                    "path": scope.get("path", ""),
                    "query": str(request.url.query),
                    "route_id": route,
                    "status": code,
                    "headers": scrub_headers(dict(request.headers)),
                    "body_b64": scrub_json_text_maybe(body_bytes.decode("utf-8", "ignore")),
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "request_id": rid,
                    "user_id": uid,
                    "default_dest": DEFAULT_DEST,
                    "timeout_secs": TIMEOUT,
                }
                try:
                    with open(JSON_PATH, "a", encoding="utf-8") as f:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                except Exception:
                    # swallow file errors (observability should not break request path)
                    pass


def install_replay_middleware(app):
    app.add_middleware(ReplayCaptureMiddleware)
