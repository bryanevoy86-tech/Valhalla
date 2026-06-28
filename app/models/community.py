"""Bridge module: re-exports from services.api.app.models.community"""
import sys
from pathlib import Path

# Ensure services/api is accessible
repo_root = Path(__file__).resolve().parent.parent.parent  # d:\dev
services_api = repo_root / "services" / "api"
if str(services_api) not in sys.path:
    sys.path.insert(0, str(services_api))

# Re-export everything from the real module
from services.api.app.models.community import *  # noqa: F401, F403
