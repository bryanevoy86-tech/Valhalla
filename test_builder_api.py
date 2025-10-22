#!/usr/bin/env python
"""Quick test script for builder API endpoints"""
import os
import sys

# Set environment variables - use SQLite for testing
os.environ["HEIMDALL_BUILDER_API_KEY"] = "your-long-random-secret"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "api"))

from fastapi.testclient import TestClient
from main import app
from app.core.db import Base, engine
from app.models.builder import BuilderTask, BuilderEvent

# Create all tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Test 1: Register
print("Testing POST /api/builder/register...")
response = client.post(
    "/api/builder/register",
    headers={"X-API-Key": "your-long-random-secret"},
    json={"agent_name": "heimdall-bot", "version": "1.0"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Create task
print("Testing POST /api/builder/tasks...")
response = client.post(
    "/api/builder/tasks",
    headers={"X-API-Key": "your-long-random-secret"},
    json={
        "title": "Add /reports router",
        "scope": "services/api/app/routers/reports.py",
        "plan": "create router with /reports/summary"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 3: List tasks
print("Testing GET /api/builder/tasks...")
response = client.get(
    "/api/builder/tasks",
    headers={"X-API-Key": "your-long-random-secret"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
