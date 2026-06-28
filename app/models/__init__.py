"""Models package - re-exports from the real application models."""
import sys
from pathlib import Path

# Ensure services/api is in sys.path so we can import from it
_this_file = Path(__file__).resolve()
_repo_root = _this_file.parent.parent.parent  # app/models -> app -> dev
_services_api = _repo_root / "services" / "api"
if str(_services_api) not in sys.path:
    sys.path.insert(0, str(_services_api))

# Now re-export everything from the real models location
# This makes 'from app.models import X' find X in services/api/app/models
try:
    from services.api.app.models import *  # noqa: F401, F403
except ImportError:
    # If this fails, that's okay - modules will be imported on-demand
    pass
