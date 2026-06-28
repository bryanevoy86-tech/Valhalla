#!/usr/bin/env python
"""Render deployment entrypoint for Valhalla API.

This script starts the FastAPI application using uvicorn.
"""
import sys
import os
from pathlib import Path

# Get the repository root
repo_root = Path(__file__).parent.resolve()

# Configure sys.path for import resolution:
# Priority 1: services/api - so 'from app.X' in routers finds services/api/app
# Priority 2: repo root - fallback for app.heimdall.routes and d:\dev\app
services_api = repo_root / "services" / "api"

# Clear any existing paths to avoid duplicates, then set clean order
sys.path = [p for p in sys.path if p not in (str(services_api), str(repo_root))]
sys.path.insert(0, str(services_api))      # index 0: services/api/app resolves to 'app'
sys.path.insert(1, str(repo_root))         # index 1: d:\dev\app resolves to 'app' (fallback)

# Ensure critical environment variables are set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///valhalla_test.db"

if "VALHALLA_JWT_SECRET" not in os.environ:
    os.environ["VALHALLA_JWT_SECRET"] = "dev-secret-key-change-in-production"

# Get port configuration
port = int(os.environ.get("PORT", 8000))
host = os.environ.get("HOST", "0.0.0.0")

# Start uvicorn with the wrapper entrypoint
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
