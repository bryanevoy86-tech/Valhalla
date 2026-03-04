"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session

from app.core.settings import settings


# Create engine with configured database
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.environment == "development",
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
