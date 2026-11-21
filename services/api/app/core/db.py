from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from .settings import settings
import logging

logger = logging.getLogger("valhalla.db")

# Database initialization MUST fail if its driver or URL is invalid.
# An implicit SQLite replacement would make the system appear operational
# while silently writing ephemeral business data to an empty database.
try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
except Exception as exc:
    logger.error("Configured database engine could not be initialized (%s)", type(exc).__name__)
    raise RuntimeError(
        "Database engine initialization failed; refusing in-memory fallback"
    ) from exc

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency for getting a database session.
    
    Ensures proper transaction handling:
    - Commits on success
    - Rolls back on exception
    - Always closes connection
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """Alias for get_db() for backwards compatibility."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_schema_initialized():
    """
    Verify that database migrations have been applied.
    
    This is called at startup to ensure:
    1. Database connection works
    2. Alembic version table exists
    3. At least one migration has been applied
    
    Raises RuntimeError if schema is not initialized.
    """
    from sqlalchemy import text, inspect
    import os
    
    # Skip verification in dev mode (DATABASE_URL starts with sqlite:)
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite"):
        logger.info("[db.verify_schema_initialized] Skipping schema check for SQLite (dev mode)")
        return
    
    try:
        with engine.connect() as conn:
            # Check if alembic_version table exists
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'alembic_version' not in tables:
                raise RuntimeError(
                    "❌ STARTUP FAILED: alembic_version table not found. "
                    "Run 'alembic upgrade head' before starting the service."
                )
            
            # Check if any migrations have been applied
            result = conn.execute(text("SELECT COUNT(*) as count FROM alembic_version"))
            row = result.fetchone()
            count = row[0] if row else 0
            
            if count == 0:
                raise RuntimeError(
                    "❌ STARTUP FAILED: No migrations applied. "
                    "Run 'alembic upgrade head' before starting the service."
                )
            
            logger.info(f"✅ Schema initialized: {count} migration(s) applied")
            
    except RuntimeError:
        raise
    except Exception as exc:
        # Returning success when a network/credential error occurs would let
        # the API run without the business ledger it expects.
        logger.error("Database schema verification failed (%s)", type(exc).__name__)
        raise RuntimeError("Database schema verification could not complete") from exc
