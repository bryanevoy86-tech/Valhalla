"""FastAPI application entry point.

Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI

app = FastAPI(title="Valhalla API", version="0.1.0")


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
"""Higher-level app entrypoints (helpers and wiring) for Valhalla application.

This file is a lightweight stub that re-exports or wraps functionality from
`app.ai` and any app-level wiring. Keep `services/api/main.py` as the HTTP
entrypoint — this `app.main` is intentionally minimal so you can import it
from other modules without bringing FastAPI into the import graph.
"""

from importlib.metadata import version

__all__ = ["version"]

try:
    __version__ = version("valhalla")
except Exception:
    __version__ = "0.0.0"

def info():
    return {"app": "Valhalla", "version": __version__}


@app.get("/hello")
def hello_get():
    return {"ok": True, "route": "/hello"}

