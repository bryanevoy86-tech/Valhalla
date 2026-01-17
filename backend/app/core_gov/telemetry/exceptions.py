import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("valhalla.unhandled")

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("UNHANDLED_EXCEPTION path=%s method=%s", request.url.path, request.method)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": type(exc).__name__},
    )
