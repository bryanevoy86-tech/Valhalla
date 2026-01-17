from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_mb: int):
        super().__init__(app)
        self.max_bytes = max_mb * 1024 * 1024

    async def dispatch(self, request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_bytes:
            return PlainTextResponse("Payload too large", status_code=413)
        return await call_next(request)
