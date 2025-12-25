import logging
import os
import contextvars

from pythonjsonlogger import jsonlogger

from .scrub import scrub_any, scrub_headers

# Context variables for request tracking
request_id_ctx = contextvars.ContextVar("request_id", default=None)
route_id_ctx = contextvars.ContextVar("route_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


class OTELJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        try:
            for key in ("headers", "payload", "body", "request", "response", "extra"):
                if key in log_record:
                    log_record[key] = scrub_any(log_record[key])
            if "headers" in log_record and isinstance(log_record["headers"], dict):
                log_record["headers"] = scrub_headers(log_record["headers"])
        except Exception:
            pass


def configure_logging():
    handler = logging.StreamHandler()
    formatter = OTELJsonFormatter()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    root.handlers = [handler]


def get_logger(name: str = "valhalla"):
    return logging.getLogger(name)
