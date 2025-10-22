from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add repo root and services/api/app to path so `from app.*` imports resolve
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
# parent of 'app' (services/api) — necessary so `import app` resolves
svc_api_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, svc_api_parent)
sys.path.insert(0, repo_root)

# Import models base using full package path so imports resolve when running
# alembic from the repo root.
from valhalla.services.api.app.core.db import Base
from valhalla.services.api.app.models.metric import Metric
from valhalla.services.api.app.models.intake import CapitalIntake

config = context.config

# Pull DATABASE_URL from environment for Render
section = config.get_section(config.config_ini_section) or {}
section["sqlalchemy.url"] = os.getenv("DATABASE_URL") or section.get("sqlalchemy.url")

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
