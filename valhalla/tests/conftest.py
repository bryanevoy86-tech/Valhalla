"""Pytest configuration - set up Python path for app imports."""
import sys
from pathlib import Path

# Add services/api to sys.path so "from app..." imports work
repo_root = Path(__file__).parent.parent
services_api = repo_root / "services" / "api"
sys.path.insert(0, str(services_api))

# Force a clean import cache for app module to avoid stale cache issues
if 'app' in sys.modules:
    del sys.modules['app']
if 'app.deal_analyzer' in sys.modules:
    del sys.modules['app.deal_analyzer']
if 'app.deal_analyzer.service' in sys.modules:
    del sys.modules['app.deal_analyzer.service']
