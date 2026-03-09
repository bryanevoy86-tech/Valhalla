import contextvars
import json
import logging
import os
import time
from logging.config import dictConfig

from opentelemetry import trace
from pythonjsonlogger import jsonlogger

LOG_ENABLED = os.getenv("LOG_ENABLED", "false").lower() in ("1", "true", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SHIP_MODE = os.getenv("LOG_SHIP_MODE", "stdout").lower()  # stdout|file|both
LOG_PATH = os.getenv("LOG_JSON_PATH", "./app.jsonl")
ROTATE_MB = int(os.getenv("LOG_JSON_ROTATE_MB", "20"))
BACKUPS = int(os.getenv("LOG_JSON_BACKUPS", "5"))
INCLUDE_HEADERS = os.getenv("LOG_INCLUDE_HEADERS", "false").lower() in ("1", "true", "yes")

# request-scoped IDs
request_id_ctx = contextvars.ContextVar("request_id", default=None)
route_id_ctx = contextvars.ContextVar("route_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


def _otel_ids():
    # pull current span context if present
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if not ctx or not ctx.is_valid:
        return None, None
    trace_id = format(ctx.trace_id, "032x")
    span_id = format(ctx.span_id, "016x")
    return trace_id, span_id


class OTELJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # standard fields
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("ts", int(time.time() * 1000))
        # correlation
        tid, sid = _otel_ids()
        if tid:
            log_record["trace_id"] = tid
        if sid:
            log_record["span_id"] = sid
        rid = request_id_ctx.get()
        if rid:
            log_record["request_id"] = rid
        route = route_id_ctx.get()
        if route:
            log_record["route_id"] = route
        uid = user_id_ctx.get()
        if uid:
            log_record["user_id"] = uid
        # ensure message is json-serializable
        try:
            json.dumps(log_record)
        except Exception:
            # fallback: stringify non-serializable fields
            for k, v in list(log_record.items()):
                try:
                    json.dumps(v)
                except Exception:
                    log_record[k] = str(v)


def configure_logging():
    if not LOG_ENABLED:
        return

    handlers = {}
    root_handlers = []

    # stdout handler
    if SHIP_MODE in ("stdout", "both"):
        handlers["stdout"] = {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "json",
            "stream": "ext://sys.stdout",
        }
        root_handlers.append("stdout")

    # file rotating handler
    if SHIP_MODE in ("file", "both"):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": LOG_LEVEL,
            "formatter": "json",
            "filename": LOG_PATH,
            "maxBytes": ROTATE_MB * 1024 * 1024,
            "backupCount": BACKUPS,
            "encoding": "utf-8",
        }
        root_handlers.append("file")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": OTELJsonFormatter,
                    "fmt": "%(message)s",
                }
            },
            "handlers": handlers,
            "root": {
                "level": LOG_LEVEL,
                "handlers": root_handlers or ["stdout"],
            },
        }
    )


# lightweight helpers
def get_logger(name: str = "valhalla"):
    return logging.getLogger(name)


# middleware helper to set contextual ids
def set_request_context(request_id: str | None, route_id: str | None, user_id: str | None = None):
    if request_id is not None:
        request_id_ctx.set(request_id)
    if route_id is not None:
        route_id_ctx.set(route_id)
    if user_id is not None:
        user_id_ctx.set(user_id)
