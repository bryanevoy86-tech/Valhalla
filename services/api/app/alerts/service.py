from typing import List
from datetime import datetime

from app.metrics.schemas import MetricsOut
from .schemas import AlertOut


class AlertsService:
    """Check metrics against thresholds and generate alerts."""

    @staticmethod
    def check_thresholds(metrics: MetricsOut) -> List[AlertOut]:
        """
        Compare metrics to thresholds and return alerts if exceeded.
        
        Thresholds:
        - error_rate > 0.1 (10%)
        - p50_latency > 1.0 (seconds)
        """
        alerts = []
        now = datetime.utcnow().isoformat()

        if metrics.error_rate is not None and metrics.error_rate > 0.1:
            alerts.append(
                AlertOut(
                    alert_type="error_rate_high",
                    message=f"Error rate exceeded 10% threshold: {metrics.error_rate:.2%}",
                    triggered_at=now,
                )
            )

        if metrics.p50_latency is not None and metrics.p50_latency > 1.0:
            alerts.append(
                AlertOut(
                    alert_type="high_latency",
                    message=f"p50 latency exceeded 1.0s threshold: {metrics.p50_latency:.3f}s",
                    triggered_at=now,
                )
            )

        return alerts
