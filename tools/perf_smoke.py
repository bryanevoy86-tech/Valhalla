"""
Minimal performance smoke test to guard against regressions.
Measures p50 latency for critical endpoints and fails if threshold exceeded.

Usage:
    API_BASE=http://localhost:4000 python tools/perf_smoke.py
    API_BASE=https://valhalla-api-ha6a.onrender.com P50_MAX_MS=400 python tools/perf_smoke.py
"""

import os
import time
import statistics
import httpx
import sys

API = os.getenv("API_BASE", "http://localhost:4000")
P50_MAX_MS = int(os.getenv("P50_MAX_MS", "300"))


def time_request(endpoint: str) -> float:
    """
    Time a single request to an endpoint.
    Returns elapsed time in milliseconds.
    """
    t0 = time.perf_counter()
    r = httpx.get(f"{API}{endpoint}", timeout=10)
    r.raise_for_status()
    return (time.perf_counter() - t0) * 1000


def main():
    """
    Run performance smoke tests against critical endpoints.
    Exit code 0 if all pass, 1 if any exceed threshold.
    """
    print(f"Performance Smoke Test")
    print(f"API: {API}")
    print(f"P50 Threshold: {P50_MAX_MS}ms")
    print("-" * 50)
    
    samples = []
    endpoints = ["/healthz", "/playbooks"]
    
    for ep in endpoints:
        times = [time_request(ep) for _ in range(5)]
        p50 = statistics.median(times)
        samples_str = ', '.join(f'{x:.0f}' for x in times)
        print(f"{ep:20} p50={p50:.1f}ms (samples={samples_str})")
        samples.append(p50)
    
    worst = max(samples)
    print("-" * 50)
    
    if worst > P50_MAX_MS:
        print(f"FAIL: p50 {worst:.1f}ms exceeds {P50_MAX_MS}ms threshold")
        sys.exit(1)
    
    print(f"OK: All endpoints under {P50_MAX_MS}ms")
    sys.exit(0)


if __name__ == "__main__":
    main()
