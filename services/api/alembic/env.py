from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Ensure /app/services/api is on sys.path so 'from app.*' imports resolve
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

# Import Base from app.core.db (NOT 'valhalla')
from app.core.db import Base

# Models imported for metadata discovery
from app.models.builder import BuilderTask, BuilderEvent
from app.models.capital import CapitalIntake
from app.integrity.models import TelemetryEvent
from app.models.grants import GrantSource, GrantRecord
from app.models.match import Buyer, DealBrief
from app.models.contracts import ContractTemplate, ContractRecord
from app.models.intake import LeadIntake
from app.models.notify import Outbox
from app.loki.models import LokiReview, LokiFinding
# Research models not yet created - comment out for now
# from app.models.research import ResearchSource, ResearchDoc, ResearchQuery, Playbook

config = context.config

# Pull DATABASE_URL from environment for Render and force-set it on the config
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Ensure Alembic uses the env var rather than the fallback in alembic.ini
    config.set_main_option("sqlalchemy.url", db_url)
else:
    # Fall back to value from alembic.ini section if env var not set
    section = config.get_section(config.config_ini_section) or {}
    # no-op: section already contains sqlalchemy.url from alembic.ini

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # engine_from_config expects the section dict and a prefix such as
    # 'sqlalchemy.' to pull the URL/opts. Use the alembic config section here.
    cfg_section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
