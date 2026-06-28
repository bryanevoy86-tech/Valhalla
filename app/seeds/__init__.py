"""Seeds package - re-exports from the real application seeds."""
import sys
from pathlib import Path

# Ensure services/api is in sys.path so we can import from it
_this_file = Path(__file__).resolve()
_repo_root = _this_file.parent.parent.parent  # app/seeds -> app -> dev
_services_api = _repo_root / "services" / "api"
if str(_services_api) not in sys.path:
    sys.path.insert(0, str(_services_api))

# Now re-export everything from the real seeds location
try:
    from services.api.app.seeds import *  # noqa: F401, F403
except ImportError:
    # If this fails, that's okay - modules will be imported on-demand
    pass
