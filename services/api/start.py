#!/usr/bin/env python3
"""
Wrapper script to start the Valhalla API with proper import paths.
This bypasses uvicorn's string-based module loader that was resolving to 'valhalla' namespace.
"""
import os
import sys

# Ensure /app/services/api is first in sys.path
api_dir = '/app/services/api'
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path[:3]}")
print(f"Current directory: {os.getcwd()}")

# Import the FastAPI app
print("Importing main.app...")
from main import app

# Start uvicorn programmatically
print("Starting uvicorn...")
import uvicorn

port = int(os.environ.get('PORT', 10000))
uvicorn.run(
    app,
    host='0.0.0.0',
    port=port,
    log_level='info'
)
