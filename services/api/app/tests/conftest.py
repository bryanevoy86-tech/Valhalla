"""Isolate supplemental legacy API fixtures from the configured service database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.main import app
from app.models.decision_outcome import DecisionOutcome
from app.models.model_provider import ModelProvider
from app.models.narrative import ActiveChapter, NarrativeChapter, NarrativeEvent
from app.models.strategic_event import StrategicEvent
from app.models.strategic_mode import StrategicMode
from app.models.triggers import TriggerEvent, TriggerRule
from app.models.tuning_rules import TuningRule


@pytest.fixture(autouse=True)
def create_test_tables(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (TuningRule, TriggerRule, TriggerEvent, StrategicMode, NarrativeChapter, NarrativeEvent,
                  ActiveChapter, DecisionOutcome, StrategicEvent, ModelProvider):
        model.__table__.create(engine)

    def isolated_session():
        with Session(engine) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_session)
    try:
        yield
    finally:
        engine.dispose()


@pytest.fixture
def client():
    return TestClient(app)
