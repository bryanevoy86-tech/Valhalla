"""Test root Alembic Business Factory migration without any live DB."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "alembic/versions/20261119_factory_legacy_work_schema.py"
SPEC = importlib.util.spec_from_file_location("factory_migration", MIGRATION)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class FactoryMigrationTests(unittest.TestCase):
    def test_migration_creates_missing_tables_and_is_idempotent(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE media_contents (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"
            ))
            conn.execute(text(
                "INSERT INTO media_contents(id, title) VALUES (7, 'preserve existing data')"
            ))
            ctx = MigrationContext.configure(conn)
            ops = Operations(ctx)
            with (
                patch.object(MOD.op, "get_bind", return_value=conn),
                patch.object(MOD.op, "create_table", side_effect=ops.create_table),
                patch.object(MOD.op, "create_index", side_effect=ops.create_index),
            ):
                MOD.upgrade()
                MOD.upgrade()
            tables = set(inspect(conn).get_table_names())
            self.assertTrue({
                "media_contents",
                "legacy_instance_registry_items",
                "legacy_instance_work_items",
                "legacy_orchestration_events",
            }.issubset(tables))
            preserved = conn.execute(text("SELECT title FROM media_contents WHERE id=7")).scalar_one()
            self.assertEqual(preserved, "preserve existing data")
            indexes = {i["name"] for i in inspect(conn).get_indexes("legacy_instance_work_items")}
            self.assertIn("ix_legacy_instance_work_items_action_id", indexes)
            self.assertIn("ix_legacy_instance_work_items_idempotency_key", indexes)
        engine.dispose()

    def test_missing_media_baseline_fails_safely(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            with patch.object(MOD.op, "get_bind", return_value=conn):
                with self.assertRaisesRegex(RuntimeError, "media_contents missing"):
                    MOD.upgrade()
            self.assertNotIn("legacy_instance_work_items", inspect(conn).get_table_names())
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
