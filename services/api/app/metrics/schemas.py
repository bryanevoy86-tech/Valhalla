from pydantic import BaseModel
from typing import Optional, List


class MetricsOut(BaseModel):
    # Runtime counters
    requests_per_sec: Optional[float] = None
    error_rate: Optional[float] = None
    p50_latency: Optional[float] = None
    total_requests: Optional[int] = None
    total_errors: Optional[int] = None


class MetricsDashboardOut(BaseModel):
    role: str
    metrics: List[str]
    last_updated: str
