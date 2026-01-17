from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import get_settings

s = get_settings()
DATABASE_URL = (
    str(s.DATABASE_URL)
    if s.DATABASE_URL
    else f"postgresql+psycopg2://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}@db:5432/{s.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
