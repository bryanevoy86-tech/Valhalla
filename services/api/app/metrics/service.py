from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque, Dict, Optional

from .schemas import MetricsOut, MetricsDashboardOut
from datetime import datetime


# In-process runtime metrics storage (thread-safe)
_LOCK = threading.Lock()
_START_TIME = time.time()
_TOTAL_REQUESTS: int = 0
_TOTAL_ERRORS: int = 0
_LATENCIES: Deque[float] = deque(maxlen=1000)  # sliding window for p50


class MetricsService:
    """Collects and reports simple in-process metrics.

    - requests_per_sec: average since process start (not instantaneous)
    - error_rate: total_errors / total_requests
    - p50_latency: median of last N (up to 1000) latencies
    - totals: total counts since process start
    """

    @staticmethod
    def record_request(success: bool, latency_seconds: float) -> None:
        global _TOTAL_REQUESTS, _TOTAL_ERRORS
        with _LOCK:
            _TOTAL_REQUESTS += 1
            if not success:
                _TOTAL_ERRORS += 1
            # Guard against NaN/inf latencies
            if latency_seconds is not None and latency_seconds == latency_seconds and latency_seconds < 60.0:
                _LATENCIES.append(float(latency_seconds))

    @staticmethod
    def get_metrics() -> MetricsOut:
        now = time.time()
        with _LOCK:
            elapsed = max(1e-6, now - _START_TIME)
            rps = _TOTAL_REQUESTS / elapsed
            err_rate = (_TOTAL_ERRORS / _TOTAL_REQUESTS) if _TOTAL_REQUESTS > 0 else 0.0
            if len(_LATENCIES) > 0:
                # Compute median without extra deps
                data = sorted(_LATENCIES)
                n = len(data)
                mid = n // 2
                if n % 2 == 1:
                    p50 = float(data[mid])
                else:
                    p50 = float((data[mid - 1] + data[mid]) / 2.0)
            else:
                p50 = None
            return MetricsOut(
                requests_per_sec=rps,
                error_rate=err_rate,
                p50_latency=p50,
                total_requests=_TOTAL_REQUESTS,
                total_errors=_TOTAL_ERRORS,
            )

    @staticmethod
    def get_role_dashboard(role: str) -> MetricsDashboardOut:
        """Return a simple role-based metrics dashboard definition.

        This is intentionally lightweight and can be expanded to include
        dynamic widgets or permissions.
        """
        role_lc = (role or "").lower()
        if role_lc == "admin":
            metrics = ["total_errors", "requests_per_sec", "p50_latency", "error_rate"]
        elif role_lc == "viewer":
            metrics = ["requests_per_sec", "error_rate"]
        else:
            metrics = ["requests_per_sec"]

        return MetricsDashboardOut(
            role=role_lc or "unknown",
            metrics=metrics,
            last_updated=datetime.utcnow().isoformat(),
        )
