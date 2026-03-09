"""Thin application entrypoint for Valhalla.

⚠️ DO NOT add routers or middleware here.
This file ONLY re-exports the real FastAPI app.

The real HTTP app lives in:
    services/api/app/main.py which uses 'app' as its module name context.
"""

import os
import sys
from pathlib import Path
from importlib.metadata import version as _version
from importlib import import_module

# Register services.api.app as 'app' module BEFORE importing main
# This allows main.py internal imports like 'from app.observability' to work
_real_package = import_module("services.api.app")
sys.modules['app'] = _real_package

# Now import and get the app instance
from services.api.app.main import app


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

