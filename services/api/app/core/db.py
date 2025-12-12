from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from .settings import settings
import logging

logger = logging.getLogger("valhalla.db")

# Try to create the DB engine using the configured DATABASE_URL. If this fails
# (for example, psycopg/libpq isn't available in the test/dev environment),
# fall back to an in-memory SQLite engine so the app can import and tests can run.
try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
except Exception as e:  # pragma: no cover - runtime fallback
    logger.warning("Could not create engine for %s: %s. Falling back to sqlite in-memory.", settings.database_url, e)
    # Use StaticPool so the in-memory SQLite database is shared across
    # connections. This is important for tests that create tables at import
    # time and then use sessions which open new connections.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Alias for get_db() for backwards compatibility."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
