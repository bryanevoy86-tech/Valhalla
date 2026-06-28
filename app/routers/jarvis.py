"""Bridge module: re-exports jarvis from services.api.app.routers"""
import sys
from pathlib import Path

# Ensure services/api is in path
repo_root = Path(__file__).resolve().parent.parent.parent  # d:\dev
services_api = repo_root / "services" / "api"
if str(services_api) not in sys.path:
    sys.path.insert(0, str(services_api))

# Re-export everything from the real module
from services.api.app.routers import jarvis  # noqa: F401
