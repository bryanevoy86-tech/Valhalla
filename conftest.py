"""pytest conftest - set up module registry and app module before tests run."""
import sys
import os
from pathlib import Path

# Ensure d:\dev is in the path
dev_root = Path(__file__).parent
sys.path.insert(0, str(dev_root))

# Register services.api.app as 'app' module BEFORE any imports
# This makes 'from app.xxx' work for services.api.app.xxx 
from importlib import import_module
_real_package = import_module("services.api.app")
sys.modules['app'] = _real_package

# Now set up the pytest environment
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure environment variables are set for tests."""
    # Set test database URL if not already set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Set JWT secret if not already set
    if "VALHALLA_JWT_SECRET" not in os.environ:
        os.environ["VALHALLA_JWT_SECRET"] = "test-secret-key-for-tests"
    
    yield


@pytest.fixture
def db(request):
    """Provide an isolated SQLAlchemy session for service-layer tests."""
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

    # Pull in direct FK dependencies for selected tables.
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
    """Compatibility fixture for legacy class-style flow tests."""
    creator = getattr(request.instance, "test_01_create_lead_via_canonical_path", None)
    if callable(creator):
        return creator()
    pytest.skip("lead_id fixture is only available for legacy flow test classes")


@pytest.fixture
def deal_id(request, lead_id):
    """Compatibility fixture for legacy class-style flow tests."""
    creator = getattr(request.instance, "test_03_convert_lead_to_deal", None)
    if callable(creator):
        return creator(lead_id)
    pytest.skip("deal_id fixture is only available for legacy flow test classes")
