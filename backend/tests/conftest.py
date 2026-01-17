import sys
from pathlib import Path
import pytest

# Set up paths IMMEDIATELY before anything else can be imported
backend_path = Path(__file__).parent.parent
repo_root = Path(__file__).parent.parent.parent

# Add backend to allow `from app.core_gov...` imports
sys.path.insert(0, str(backend_path))

# Add repo root to allow `from test_gov_app` imports
sys.path.insert(0, str(repo_root))

# Change to backend directory so relative file paths work
import os
os.chdir(str(backend_path))

# Module-level variable to cache app
_app = None

def get_app():
    global _app
    if _app is None:
        from test_gov_app import app as _test_app
        _app = _test_app
    return _app

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(get_app())




