import json
import os
from dataclasses import dataclass
from typing import Dict


DEFAULT_METRICS_FILE = os.environ.get(
    "SYSTEM_METRICS_FILE",
    os.path.join(os.getcwd(), "var", "system_metrics.json"),
)


@dataclass
class SystemMetrics:
    """
    Minimal, explicit system metrics used by gates.
    Wire to real analytics later; this provides a canonical source today.
    """
    monthly_net_cad: float = 0.0
    monthly_burn_cad: float = 200.0
    critical_runbook_blockers: int = 0

    # Closed-loop learning
    outcomes_required_ratio: float = 1.0  # 1.0 = 100% outcomes required
    outcomes_recorded_ratio: float = 0.0  # computed / updated elsewhere

    # Data purity
    quarantine_backlog: int = 0
    clean_promotion_enabled: bool = True


class MetricsStore:
    def __init__(self, path: str = DEFAULT_METRICS_FILE):
        self.path = path

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def load(self) -> SystemMetrics:
        if not os.path.exists(self.path):
            return SystemMetrics()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f) or {}
            return SystemMetrics(**raw)
        except Exception:
            # fail-closed with safe defaults
            return SystemMetrics()

    def save(self, metrics: SystemMetrics) -> None:
        self._ensure_dir()
        payload = metrics.__dict__
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, self.path)
