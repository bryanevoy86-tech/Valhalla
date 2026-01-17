"""Thin application entrypoint for Valhalla.

⚠️ DO NOT add routers or middleware here.
This file ONLY re-exports the real FastAPI app.

The real HTTP app lives in:
    services/api/main.py
"""

from importlib.metadata import version as _version

# Re-export the real FastAPI app
from services.api.main import app  # noqa: F401


# ---- Metadata helpers -------------------------------------------------------

try:
    __version__ = _version("valhalla")
except Exception:
    __version__ = "0.0.0"


def info() -> dict:
    return {
        "app": "Valhalla",
        "version": __version__,
        "entrypoint": "services.api.main:app",
    }

