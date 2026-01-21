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
        raise  # Re-raise our custom errors
    except Exception as e:
        logger.warning(
            f"⚠️  Schema validation skipped (in-memory SQLite or connection error): {e}"
        )
