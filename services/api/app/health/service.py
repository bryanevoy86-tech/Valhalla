from datetime import datetime
from typing import Optional

from .schemas import HealthCheckOut
from app.metrics.service import MetricsService


class HealthCheckService:
    """Performs simple system health checks and triggers recovery if needed."""

    @staticmethod
    def check_system_health() -> HealthCheckOut:
        # Basic checks; extend with real probes as needed
        api_ok = HealthCheckService.check_api_health()
        resources_ok = HealthCheckService.check_server_resources()

        # Consider metrics: if very high error-rate, mark unhealthy
        metrics = MetricsService.get_metrics()
        error_rate = metrics.error_rate or 0.0
        metrics_ok = error_rate < 0.25  # 25% hard stop

        is_healthy = api_ok and resources_ok and metrics_ok
        recovery_note: Optional[str] = None
        if not is_healthy:
            recovery_note = HealthCheckService.trigger_recovery()

        return HealthCheckOut(
            service="System",
            status="Healthy" if is_healthy else "Unhealthy",
            last_checked=datetime.utcnow().isoformat(),
            recovery_action_taken=recovery_note,
        )

    @staticmethod
    def check_api_health() -> bool:
        # Could call internal /api/health; for now assume ok while service is up
        return True

    @staticmethod
    def check_server_resources() -> bool:
        # Placeholder for CPU/memory/disk checks
        return True

    @staticmethod
    def trigger_recovery() -> str:
        # Placeholder action; could restart workers, clear caches, etc.
        # Return a short description for auditing
        return "Recovery triggered: no-op"
