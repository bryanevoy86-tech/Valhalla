from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session
from sqlalchemy.pool import StaticPool
from .config import settings
import logging

logger = logging.getLogger("valhalla.db")

# Try to create the DB engine using the configured DATABASE_URL. If this fails
# (for example, psycopg/libpq isn't available in the test/dev environment),
# fall back to an in-memory SQLite engine so the app can import and tests can run.
try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
except Exception as e:  # pragma: no cover - runtime fallback
    logger.warning("Could not create engine for %s: %s. Falling back to sqlite in-memory.", settings.DATABASE_URL, e)
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


# Best-effort: import all models in this package so they register with Base.metadata
# and then create tables on the engine used by this module. This avoids a situation
# where tests import the app before models are otherwise imported, leading to
# `no such table` errors when using an in-memory SQLite engine.
try:  # pragma: no cover - runtime safety
    # Import model modules so their Table objects register on Base.metadata.
    # Use explicit imports (simple and reliable) instead of dynamic pkgutil logic
    # which can be brittle when __package__ is None during some import paths.
    from ..models import metric, intake  # noqa: F401
except Exception:
    logger.debug("Could not import models package for automatic table creation", exc_info=True)

try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured in db module")
except Exception:
    logger.exception("db.metadata.create_all failed")
