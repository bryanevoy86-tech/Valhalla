"""pytest conftest - set up module registry and app module before tests run."""
import sys
import os
from pathlib import Path

# Ensure d:\dev is in the path
dev_root = Path(__file__).parent
sys.path.insert(0, str(dev_root))

# Register services.api.app as 'app' module BEFORE any imports
# This makes 'from app.xxx' work for services.api.app.xxx 
from importlib import import_module
_real_package = import_module("services.api.app")
sys.modules['app'] = _real_package

# Now set up the pytest environment
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure environment variables are set for tests."""
    # Set test database URL if not already set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Set JWT secret if not already set
    if "VALHALLA_JWT_SECRET" not in os.environ:
        os.environ["VALHALLA_JWT_SECRET"] = "test-secret-key-for-tests"
    
    yield
