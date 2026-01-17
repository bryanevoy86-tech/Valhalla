from __future__ import annotations

from fastapi import Depends, Request

from ..rate_limit.limiter import RateLimit, check_rate_limit

def rate_limit(bucket_name: str, max_requests: int, window_seconds: int):
    rl = RateLimit(max_requests=max_requests, window_seconds=window_seconds)

    def dep(request: Request):
        check_rate_limit(request, bucket_name=bucket_name, rl=rl)

    return Depends(dep)
