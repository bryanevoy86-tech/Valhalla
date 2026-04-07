"""
PACK TU: Global Error & ProblemDetails Engine
Registers structured error handlers for the whole FastAPI app.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import ProblemDetails


def _get_correlation_id(request: Request) -> str | None:
    """Extract correlation ID from request state or headers."""
    # Set by correlation middleware (PACK TW). Fall back to header if needed.
    cid = getattr(request.state, "correlation_id", None)
    if cid:
        return cid
    return request.headers.get("X-Request-ID")


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    cid = _get_correlation_id(request)
    problem = ProblemDetails(
        type="about:blank",
        title=exc.detail if isinstance(exc.detail, str) else "HTTP error",
        status=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else None,
        instance=str(request.url),
        correlation_id=cid,
    )
    return JSONResponse(status_code=exc.status_code, content=problem.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with detailed error list."""
    cid = _get_correlation_id(request)
    problem = ProblemDetails(
        type="https://valhalla/errors/validation",
        title="Validation error",
        status=422,
        detail="One or more fields failed validation.",
        instance=str(request.url),
        correlation_id=cid,
        extra={"errors": exc.errors()},
    )
    return JSONResponse(status_code=422, content=problem.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    cid = _get_correlation_id(request)
    problem = ProblemDetails(
        type="https://valhalla/errors/internal",
        title="Internal server error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url),
        correlation_id=cid,
    )
    return JSONResponse(status_code=500, content=problem.model_dump())


def register_error_handlers(app) -> None:
    """
    Register error handlers with FastAPI app.
    Call this in main.py after creating the FastAPI app instance.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
