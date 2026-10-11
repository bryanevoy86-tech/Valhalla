"""Pytest configuration and shared fixtures for canonical backend tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Add repo root so "from app..." imports resolve in both root and service tests.
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@pytest.fixture
def db(request):
    """Provide an isolated SQLite session for tests that need a SQLAlchemy Session."""
    from app.core.db import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    module = getattr(request, "module", None)
    selected_tables = set()

    if module is not None:
        for value in vars(module).values():
            table = getattr(value, "__table__", None)
            if table is not None:
                selected_tables.add(table)

    changed = True
    while changed:
        changed = False
        for table in list(selected_tables):
            for fk in table.foreign_keys:
                dep = fk.column.table
                if dep not in selected_tables:
                    selected_tables.add(dep)
                    changed = True

    create_tables = list(selected_tables) if selected_tables else list(Base.metadata.tables.values())
    Base.metadata.create_all(bind=engine, tables=create_tables)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine, tables=create_tables)


@pytest.fixture
def lead_id(request):
    """Compatibility fixture for legacy class-based flow tests expecting lead_id."""
    creator = getattr(request.instance, "test_01_create_lead_via_canonical_path", None)
    if callable(creator):
        return creator()
    pytest.skip("lead_id fixture is only available for legacy flow test classes")


@pytest.fixture
def deal_id(request, lead_id):
    """Compatibility fixture for legacy class-based flow tests expecting deal_id."""
    creator = getattr(request.instance, "test_03_convert_lead_to_deal", None)
    if callable(creator):
        return creator(lead_id)
    pytest.skip("deal_id fixture is only available for legacy flow test classes")
