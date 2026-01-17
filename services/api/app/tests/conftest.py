"""
Pytest configuration for the API tests.
Creates test database tables for CI5-CI8 and CL9-CL12 packs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.db import engine
from app.main import app

# Import CI models to ensure they're registered
from app.models.tuning_rules import TuningProfile, TuningConstraint
from app.models.triggers import TriggerRule, TriggerEvent  
from app.models.strategic_mode import StrategicMode, ActiveMode
from app.models.narrative import NarrativeChapter, NarrativeEvent, ActiveChapter

# Import CL models
from app.models.decision_outcome import DecisionOutcome
from app.models.strategic_event import StrategicEvent
from app.models.model_provider import ModelProvider


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all test database tables once per session using the app's engine."""
    # Create CI5-CI8 tables
    TuningProfile.__table__.create(engine, checkfirst=True)
    TuningConstraint.__table__.create(engine, checkfirst=True)
    TriggerRule.__table__.create(engine, checkfirst=True)
    TriggerEvent.__table__.create(engine, checkfirst=True)
    StrategicMode.__table__.create(engine, checkfirst=True)
    ActiveMode.__table__.create(engine, checkfirst=True)
    NarrativeChapter.__table__.create(engine, checkfirst=True)
    NarrativeEvent.__table__.create(engine, checkfirst=True)
    ActiveChapter.__table__.create(engine, checkfirst=True)
    
    # Create CL9-CL12 tables
    DecisionOutcome.__table__.create(engine, checkfirst=True)
    StrategicEvent.__table__.create(engine, checkfirst=True)
    ModelProvider.__table__.create(engine, checkfirst=True)
    
    yield
    
    # Cleanup after all tests
    with engine.begin() as conn:
        # CL12
        conn.execute(text("DROP TABLE IF EXISTS model_providers"))
        # CL11
        conn.execute(text("DROP TABLE IF EXISTS strategic_events"))
        # CL9
        conn.execute(text("DROP TABLE IF EXISTS decision_outcomes"))
        # CI8
        conn.execute(text("DROP TABLE IF EXISTS active_chapters"))
        conn.execute(text("DROP TABLE IF EXISTS narrative_events"))
        conn.execute(text("DROP TABLE IF EXISTS narrative_chapters"))
        # CI7
        conn.execute(text("DROP TABLE IF EXISTS active_modes"))
        conn.execute(text("DROP TABLE IF EXISTS strategic_modes"))
        # CI6
        conn.execute(text("DROP TABLE IF EXISTS trigger_events"))
        conn.execute(text("DROP TABLE IF EXISTS trigger_rules"))
        # CI5
        conn.execute(text("DROP TABLE IF EXISTS tuning_constraints"))
        conn.execute(text("DROP TABLE IF EXISTS tuning_profiles"))


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


