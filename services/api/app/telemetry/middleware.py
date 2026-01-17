from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.db import SessionLocal
from .service import TelemetryService
from .schemas import TelemetryIn
import traceback

class TelemetryExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Best-effort log; avoid crashing if DB has issues
            try:
                db = SessionLocal()
                TelemetryService(db).write(TelemetryIn(event='http.exception', level='error', actor='api', meta={
                    'path': str(request.url),
                    'method': request.method,
                    'error': str(e),
                    'trace': ''.join(traceback.format_exc())[:4000]
                }))
                db.close()
            except Exception:
                pass
            raise
