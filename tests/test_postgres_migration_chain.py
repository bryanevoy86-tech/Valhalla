"""Replay new Factory + JWT revocation migrations on disposable PostgreSQL.

Never run on a live Render database. This test explicitly restricts the URL
to a local CI database and preserves a preexisting media-content record.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
url = os.environ.get("FACTORY_TEST_POSTGRES_URL", "")
if url and not url.endswith("@127.0.0.1:5432/valhalla_factory_ci"):
    raise RuntimeError("PostgreSQL migration test refuses non-disposable database URL")


def load(path: str):
    source = ROOT / path
    name = source.stem
    spec = importlib.util.spec_from_file_location(name, source)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FACTORY = load("alembic/versions/20261119_factory_legacy_work_schema.py")
REVOCATION = load("alembic/versions/20261119_persistent_auth_revocation.py")


@unittest.skipUnless(url, "Disposable PostgreSQL database not supplied")
class PostgresMigrationChainTests(unittest.TestCase):
    def test_migrations_preserve_baseline_and_repeat_without_duplicate_tables(self):
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE media_contents (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"))
                conn.execute(text("INSERT INTO media_contents(id,title) VALUES(9,'keep preexisting content')"))
                operations = Operations(MigrationContext.configure(conn))
                for module in (FACTORY, REVOCATION):
                    with (
                        patch.object(module.op, "get_bind", return_value=conn),
                        patch.object(module.op, "create_table", side_effect=operations.create_table),
                        patch.object(module.op, "create_index", side_effect=operations.create_index),
                    ):
                        module.upgrade()
                        module.upgrade()
                tables = set(inspect(conn).get_table_names())
                for expected in (
                    "legacy_instance_registry_items",
                    "legacy_instance_work_items",
                    "legacy_orchestration_events",
                    "auth_revoked_access_tokens",
                ):
                    self.assertIn(expected, tables)
                self.assertEqual(
                    conn.execute(text("SELECT title FROM media_contents WHERE id=9")).scalar_one(),
                    "keep preexisting content",
                )
                indexes = {
                    item["name"] for item in inspect(conn).get_indexes("auth_revoked_access_tokens")
                }
                self.assertIn("ix_auth_revoked_access_tokens_jti_sha256", indexes)
        finally:
            engine.dispose()

        # The dedicated Postgres service is discarded after this job.
        # Never drop a DB simply because this schema test completed.


if __name__ == "__main__":
    unittest.main()
