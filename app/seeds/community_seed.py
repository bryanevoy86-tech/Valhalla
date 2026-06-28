"""Bridge module: re-exports from services.api.app.seeds.community_seed"""
import sys
from pathlib import Path

# Construct absolute path to services/api
current_file = Path(__file__).resolve()  # d:\dev\app\seeds\community_seed.py
repo_root = current_file.parent.parent.parent  # d:\dev
services_api = repo_root / "services" / "api"

# Ensure services/api is in sys.path
if str(services_api) not in sys.path:
    sys.path.insert(0, str(services_api))

# Re-export everything from the real module
from services.api.app.seeds.community_seed import *  # noqa: F401, F403
