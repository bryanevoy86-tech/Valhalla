#!/usr/bin/env python
"""Initialize database schema from SQLAlchemy models."""
import os
import sys

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///./valhalla_local.db'
os.environ['VALHALLA_JWT_SECRET'] = 'dev-secret-key'

sys.path.insert(0, 'services/api')

from app.core.db import Base, engine
from app import models

# Create all tables from models
Base.metadata.create_all(bind=engine)
print("✅ Database schema initialized from models")
