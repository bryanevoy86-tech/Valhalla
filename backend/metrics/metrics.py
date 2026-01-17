from __future__ import annotations

import os

from prometheus_client import Counter, Gauge, Histogram

METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

API_REQUESTS = Counter("api_requests_total", "Total API requests", ["method", "path", "status"])
API_LATENCY = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "path", "status"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
EXPORT_ENQUEUED = Counter("export_enqueued_total", "Jobs enqueued", ["job_type", "org_id"])
EXPORT_IN_PROGRESS = Gauge("export_in_progress", "Jobs currently processing", ["org_id"])
EXPORT_COMPLETED = Counter("export_completed_total", "Jobs completed", ["job_type", "org_id"])
EXPORT_FAILED = Counter("export_failed_total", "Jobs failed", ["job_type", "org_id", "reason"])
EXPORT_RETRYING = Counter(
    "export_retrying_total", "Jobs scheduled for retry", ["job_type", "org_id"]
)
EXPORT_DURATION = Histogram(
    "export_duration_seconds",
    "Export end-to-end duration (processing window)",
    ["job_type", "org_id"],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1200),
)
EXPORT_DOWNLOADS = Counter("export_downloads_total", "Successful export downloads", ["org_id"])
EXPORT_DOWNLOADS_DENIED = Counter(
    "export_downloads_denied_total", "Denied downloads", ["org_id", "reason"]
)
SSE_CONNECTIONS = Gauge("sse_connections", "Active SSE connections")
WEBHOOK_SENT = Counter("webhook_sent_total", "Webhooks sent", ["event_type"])
WEBHOOK_FAILED = Counter("webhook_failed_total", "Webhooks failed", ["event_type"])
WEBHOOK_LATENCY = Histogram(
    "webhook_duration_seconds",
    "Webhook POST latency",
    ["event_type"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
MALWARE_DETECTED = Counter("export_malware_detected_total", "Malware detections", ["org_id"])
CLEANUP_DELETIONS = Counter(
    "export_cleanup_deleted_total", "Files deleted by cleanup", ["org_id", "reason"]
)
