#!/usr/bin/env python
"""Mark bootstrap migration as applied without running it."""
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./valhalla_local.db')
with engine.connect() as conn:
    try:
        conn.execute(text("INSERT OR IGNORE INTO alembic_version (version_num) VALUES ('9999_bootstrap_core')"))
        conn.execute(text("INSERT OR IGNORE INTO alembic_version (version_num) VALUES ('add_community_templates_and_logs_20260407')"))
        conn.commit()
        print("✅ Bootstrap migrations marked as applied")
    except Exception as e:
        print(f"Note: {e}")
        conn.rollback()
