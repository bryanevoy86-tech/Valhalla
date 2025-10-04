import json
import os
import threading
from collections import deque
from collections.abc import Iterable
from typing import Any, Dict, Optional

from app.observability.scrub import scrub_any
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() in ("1", "true", "yes")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "valhalla-backend")
JSON_PATH = os.getenv("OTEL_JSON_PATH", "./traces.jsonl")
MAX_INMEM = int(os.getenv("OTEL_MAX_INMEM_SPANS", "5000"))

OTLP_ENABLED = os.getenv("OTEL_OTLP_ENABLED", "false").lower() in ("1", "true", "yes")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
OTLP_INSECURE = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() in ("1", "true", "yes")


# ---- In-memory ring-buffer exporter (for Admin UI) ----
class RingBufferExporter(SpanExporter):
    def __init__(self, max_spans: int = 5000):
        self._buf = deque(maxlen=max_spans)
        self._lock = threading.Lock()

    def export(self, spans: Iterable[ReadableSpan]) -> "SpanExportResult":
        with self._lock:
            for s in spans:
                self._buf.append(self._to_dict(s))
        return SpanExportResult.SUCCESS

    def shutdown(self):
        with self._lock:
            self._buf.clear()

    def get_spans(
        self,
        limit: int = 200,
        name: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        since_ms: Optional[int] = None,
    ):
        with self._lock:
            items = list(self._buf)[-limit:]
        if name:
            items = [s for s in items if s.get("name") == name]
        if kind:
            items = [s for s in items if s.get("kind") == kind]
        if status:
            items = [s for s in items if s.get("status", {}).get("status_code") == status]
        if since_ms:
            items = [s for s in items if s.get("start_time_unix_nano", 0) // 1_000_000 >= since_ms]
        return items

    def _to_dict(self, span: ReadableSpan) -> Dict[str, Any]:
        ctx = span.get_span_context()
        attrs = {}
        if span.attributes:
            for k, v in span.attributes.items():
                try:
                    json.dumps(v)  # ensure serializable
                    attrs[k] = v
                except Exception:
                    attrs[k] = str(v)
        events = []
        for e in span.events:
            ev_attrs = {}
            if e.attributes:
                for k, v in e.attributes.items():
                    try:
                        json.dumps(v)
                        ev_attrs[k] = v
                    except Exception:
                        ev_attrs[k] = str(v)
            events.append(
                {"name": e.name, "attributes": ev_attrs, "timestamp_unix_nano": e.timestamp}
            )
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
            "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
            "name": span.name,
            "kind": str(span.kind).split(".")[-1],
            "status": {"status_code": str(span.status.status_code).split(".")[-1]},
            "start_time_unix_nano": span.start_time,
            "end_time_unix_nano": span.end_time,
            "attributes": attrs,
            "events": events,
            "resource": {"service.name": SERVICE_NAME},
        }


# ---- JSON lines file exporter ----
class JsonFileExporter(SpanExporter):
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def export(self, spans: Iterable[ReadableSpan]) -> "SpanExportResult":
        with open(self.path, "a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps(RING_EXPORTER._to_dict(s)) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        # nothing special
        return


RING_EXPORTER = RingBufferExporter(max_spans=MAX_INMEM)
FILE_EXPORTER = JsonFileExporter(JSON_PATH)


def setup_tracing(app: FastAPI):
    if not OTEL_ENABLED:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    provider.add_span_processor(BatchSpanProcessor(RING_EXPORTER))
    provider.add_span_processor(BatchSpanProcessor(FILE_EXPORTER))
    if OTLP_ENABLED:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces", insecure=OTLP_INSECURE)
            )
        )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = "valhalla"):
    return trace.get_tracer(name)


# Decorator helper for jobs / functions
from functools import wraps


def trace_span(name: Optional[str] = None, **attrs):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(fn.__module__)
            with tracer.start_as_current_span(name or fn.__name__) as span:
                if attrs:
                    for k, v in attrs.items():
                        span.set_attribute(k, scrub_any(v))
                return fn(*args, **kwargs)

        return wrapper

    return deco
