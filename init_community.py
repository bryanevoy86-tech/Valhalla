#!/usr/bin/env python
"""Initialize community database tables and seed data."""
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

# Set environment  
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///valhalla_test.db"
if "VALHALLA_JWT_SECRET" not in os.environ:
    os.environ["VALHALLA_JWT_SECRET"] = "dev-test-secret-key-12345"

# Now import and create
from app.core.db import Base, engine, get_db
from app.models import community as community_models
from app.seeds import community_seed
from sqlalchemy.orm import Session

print("Creating community database tables...")
Base.metadata.create_all(engine)
print("✓ Tables created")

print("Seeding test data...")
db = Session(engine)
try:
    community_seed.seed_community(db)
    print("✓ Seed data loaded")
finally:
    db.close()
    
print("\nCommunity module is ready!")
