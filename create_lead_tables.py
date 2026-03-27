#!/usr/bin/env python
"""
Create lead acquisition engine tables directly using SQLAlchemy.
"""

import os
import sys

# Change to correct directory
os.chdir('d:/dev/services/api')
sys.path.insert(0, 'd:/dev/services/api')

# Set up environment
os.environ['VALHALLA_JWT_SECRET'] = 'dev-secret'
os.environ['DATABASE_URL'] = 'sqlite:///./backend_validation.db'

from app.core.db import Base, engine
from app.models.lead_source import LeadSource
from app.models.raw_lead import RawLead
from app.models.normalized_lead import NormalizedLead

print("=" * 80)
print("CREATING LEAD ACQUISITION ENGINE TABLES")
print("=" * 80)

try:
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("\n✅ Tables created successfully:")
    print(f"   - lead_sources")
    print(f"   - raw_leads")
    print(f"   - normalized_leads")
    print("\n✅ Lead acquisition engine tables are ready!")
    print("=" * 80)
except Exception as e:
    print(f"\n❌ Error creating tables: {e}")
    sys.exit(1)
