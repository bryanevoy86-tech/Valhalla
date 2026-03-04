"""
Pytest configuration and fixtures for API testing.
"""
import pytest
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from app.core.db import engine, SessionLocal, Base
from app.models.activation_gate import ActivationGate


def pytest_configure(config):
    """Create tables before running tests."""
    Base.metadata.create_all(engine)


@pytest.fixture(scope="function")
def db():
    """Provide a clean database session for each test."""
    db_session = SessionLocal()
    
    yield db_session
    
    # Cleanup: clear all data and close session
    db_session.close()


@pytest.fixture(scope="function")
def client():
    """Provide a test client with database dependency injection."""
    from app.main import app as test_app
    from app.core.db import get_db
    
    def override_get_db():
        # Create fresh session for each test/request
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    # Clear all tables before test
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    with TestClient(test_app) as test_client:
        yield test_client
    
    # Cleanup: drop all tables after test
    Base.metadata.drop_all(engine)
    test_app.dependency_overrides.clear()
