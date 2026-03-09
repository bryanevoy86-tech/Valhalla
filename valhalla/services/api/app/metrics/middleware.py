from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from time import time as _time

from .service import MetricsService


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = _time()
        response: Response = await call_next(request)
        latency_seconds = _time() - start_time
        MetricsService.record_request(
            success=(response.status_code < 400),
            latency_seconds=latency_seconds,
        )
        return response
