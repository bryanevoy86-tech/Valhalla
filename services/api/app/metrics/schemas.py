from pydantic import BaseModel
from typing import Optional


class MetricsOut(BaseModel):
    # Runtime counters
    requests_per_sec: Optional[float] = None
    error_rate: Optional[float] = None
    p50_latency: Optional[float] = None
    total_requests: Optional[int] = None
    total_errors: Optional[int] = None
