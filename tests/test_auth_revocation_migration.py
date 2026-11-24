"""Additive WeWeb revoked-token schema migration without touching live DB."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "alembic/versions/20261119_persistent_auth_revocation.py"
spec = importlib.util.spec_from_file_location("revocation_migration", MIGRATION)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RevocationSchemaTests(unittest.TestCase):
    def test_upgrade_creates_durable_unique_index_without_data_loss(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE baseline (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"))
            conn.execute(text("INSERT INTO baseline(id, value) VALUES(1, 'keep')"))
            op = Operations(MigrationContext.configure(conn))
            with (
                patch.object(module.op, "get_bind", return_value=conn),
                patch.object(module.op, "create_table", side_effect=op.create_table),
                patch.object(module.op, "create_index", side_effect=op.create_index),
            ):
                module.upgrade()
                module.upgrade()
            self.assertIn("auth_revoked_access_tokens", inspect(conn).get_table_names())
            self.assertEqual(conn.execute(text("SELECT value FROM baseline WHERE id=1")).scalar_one(), "keep")
            names = {i["name"] for i in inspect(conn).get_indexes("auth_revoked_access_tokens")}
            self.assertIn("ix_auth_revoked_access_tokens_jti_sha256", names)
            self.assertIn("ix_auth_revoked_access_tokens_user_id", names)
        engine.dispose()

    def test_downgrade_does_not_restore_revoked_tokens(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            op = Operations(MigrationContext.configure(conn))
            with (
                patch.object(module.op, "get_bind", return_value=conn),
                patch.object(module.op, "create_table", side_effect=op.create_table),
                patch.object(module.op, "create_index", side_effect=op.create_index),
            ):
                module.upgrade()
                module.downgrade()
            self.assertTrue(inspect(conn).has_table("auth_revoked_access_tokens"))
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
