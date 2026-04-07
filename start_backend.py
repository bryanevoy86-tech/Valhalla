#!/usr/bin/env python
"""Start the Valhalla backend with proper module setup."""
import sys
import os
from pathlib import Path
from importlib import import_module

# Ensure paths are set up
dev_root = Path(__file__).parent
sys.path.insert(0, str(dev_root))
sys.path.insert(0, str(dev_root / "services" / "api"))

# Register services.api.app as 'app' module
_real_package = import_module("services.api.app")
sys.modules['app'] = _real_package

# Set environment if needed
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///valhalla_test.db"
if "VALHALLA_JWT_SECRET" not in os.environ:
    os.environ["VALHALLA_JWT_SECRET"] = "dev-test-secret-key-12345"

# Get port from command line or environment
port = 4000
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        pass
if "BACKEND_PORT" in os.environ:
    try:
        port = int(os.environ["BACKEND_PORT"])
    except ValueError:
        pass

# Now start uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=False,  # Disable reload to avoid module re-registration complexity
        log_level="info"
    )
